"""MCP wiring and command-line entry point."""

from __future__ import annotations

import argparse
import asyncio
import hmac
import json
import logging
import os
import sys
from pathlib import Path
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from . import __version__
from .core import AISLOPError, Workspace

LOG = logging.getLogger("aislop")
TIMEOUT = 30


def create_server(workspace: Workspace, *, host: str = "127.0.0.1", port: int = 8000) -> FastMCP:
    """Create the SDK server and register exactly the specified three tools."""
    server = FastMCP(
        "AISLOP", instructions="Bounded, read-only workspace inspection.",
        host=host, port=port, streamable_http_path="/mcp", stateless_http=True,
        json_response=True,
    )

    async def invoke(operation, **arguments):
        try:
            async with asyncio.timeout(TIMEOUT):
                return await operation(**arguments)
        except TimeoutError as exc:
            raise ToolError(_error_json("TIMEOUT", "tool deadline exceeded", True)) from exc
        except asyncio.CancelledError as exc:
            raise ToolError(_error_json("CANCELLED", "tool call was cancelled", True)) from exc
        except AISLOPError as exc:
            raise ToolError(json.dumps(exc.payload, separators=(",", ":"))) from exc

    @server.tool()
    async def inspect_path(
        path: Annotated[str, Field(min_length=1)], include_content: bool = False,
        max_bytes: Annotated[int, Field(ge=1, le=1_048_576)] = 65_536,
        max_entries: Annotated[int, Field(ge=1, le=1000)] = 200,
    ) -> dict[str, Any]:
        """Return metadata and optionally bounded content or directory entries."""
        return await invoke(workspace.inspect_path, path=path, include_content=include_content,
                            max_bytes=max_bytes, max_entries=max_entries)

    @server.tool()
    async def scan_text(
        path: Annotated[str, Field(min_length=1)],
        query: Annotated[str, Field(min_length=1, max_length=4096)],
        mode: Annotated[str, Field(pattern="^(literal|regex)$")] = "literal",
        case_sensitive: bool = True, glob: str = "**/*",
        max_results: Annotated[int, Field(ge=1, le=1000)] = 100,
    ) -> dict[str, Any]:
        """Search regular UTF-8 files with a literal or RE2-compatible pattern."""
        return await invoke(workspace.scan_text, path=path, query=query, mode=mode,
                            case_sensitive=case_sensitive, glob=glob, max_results=max_results)

    @server.tool()
    async def observe_changes(
        path: Annotated[str, Field(min_length=1)], cursor: str | None = None,
        glob: str = "**/*", max_changes: Annotated[int, Field(ge=1, le=1000)] = 200,
    ) -> dict[str, Any]:
        """Create a metadata cursor or compare and replace an existing cursor."""
        return await invoke(workspace.observe_changes, path=path, cursor=cursor,
                            glob=glob, max_changes=max_changes)

    return server


class HTTPPolicy:
    """ASGI middleware for bearer auth, body limits, health, and request timeout."""

    def __init__(self, app, token: str, max_body: int, timeout: float):
        self.app, self.token, self.max_body, self.timeout = app, token, max_body, timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        if path in ("/health", "/healthz"):
            return await _response(send, 200, b'{"status":"ok"}')
        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        expected = b"Bearer " + self.token.encode()
        if not hmac.compare_digest(headers.get(b"authorization", b""), expected):
            return await _response(send, 401, b'{"error":"unauthorized"}')
        length = headers.get(b"content-length")
        if length:
            try:
                if int(length) > self.max_body:
                    return await _response(send, 413, b'{"error":"request too large"}')
            except ValueError:
                return await _response(send, 400, b'{"error":"invalid content-length"}')
        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.max_body:
                raise _BodyTooLarge
            return message

        try:
            async with asyncio.timeout(self.timeout):
                await self.app(scope, limited_receive, send)
        except _BodyTooLarge:
            await _response(send, 413, b'{"error":"request too large"}')
        except TimeoutError:
            await _response(send, 504, b'{"error":"request timeout"}')


class _BodyTooLarge(Exception):
    pass


async def _response(send, status: int, body: bytes):
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode())]})
    await send({"type": "http.response.body", "body": body})


def _error_json(code: str, message: str, retryable: bool = False) -> str:
    return json.dumps({"code": code, "message": message, "retryable": retryable}, separators=(",", ":"))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="aislop", description="Run the AISLOP MCP server.")
    result.add_argument("--version", action="version", version=f"aislop {__version__}")
    result.add_argument("--allow-root", action="append", type=Path, required=True,
                        help="absolute readable workspace root (repeatable)")
    result.add_argument("--transport", choices=("stdio", "http"), default="stdio")
    result.add_argument("--host", default="127.0.0.1", help="HTTP bind host (default: loopback)")
    result.add_argument("--port", type=int, default=8000, help="HTTP port (default: 8000)")
    result.add_argument("--auth-token", help="HTTP bearer token (or AISLOP_AUTH_TOKEN)")
    result.add_argument("--max-request-bytes", type=int, default=1_048_576)
    result.add_argument("--request-timeout", type=float, default=35.0)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s")
    if any(not root.is_absolute() for root in args.allow_root):
        parser().error("--allow-root values must be absolute paths")
    if args.max_request_bytes < 1 or args.request_timeout <= 0:
        parser().error("HTTP size and timeout limits must be positive")
    try:
        workspace = Workspace(args.allow_root)
    except (OSError, ValueError) as exc:
        parser().error(f"invalid --allow-root: {exc}")
    server = create_server(workspace, host=args.host, port=args.port)
    if args.transport == "stdio":
        server.run(transport="stdio")
        return 0
    token = args.auth_token or os.environ.get("AISLOP_AUTH_TOKEN")
    if not token:
        parser().error("HTTP requires --auth-token or AISLOP_AUTH_TOKEN")
    if args.host not in {"127.0.0.1", "::1", "localhost"} and len(token) < 32:
        parser().error("non-loopback HTTP requires a bearer token of at least 32 characters")
    import uvicorn
    app = HTTPPolicy(server.streamable_http_app(), token, args.max_request_bytes, args.request_timeout)
    uvicorn.run(app, host=args.host, port=args.port, log_config=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
