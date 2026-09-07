import asyncio
import json
from pathlib import Path

import pytest

import aislop.server as server_module
from aislop.core import Workspace
from aislop.server import HTTPPolicy, create_server


async def request(app, *, path="/mcp", headers=(), body=b""):  # type: ignore[no-untyped-def]
    sent: list[dict] = []
    delivered = False

    async def receive():  # type: ignore[no-untyped-def]
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):  # type: ignore[no-untyped-def]
        sent.append(message)

    scope = {
        "type": "http",
        "path": path,
        "headers": list(headers),
        "method": "POST",
        "client": ("127.0.0.1", 1234),
    }
    await app(scope, receive, send)
    status = next(item["status"] for item in sent if item["type"] == "http.response.start")
    payload = b"".join(item.get("body", b"") for item in sent)
    return status, json.loads(payload)


@pytest.mark.asyncio
async def test_http_health_authentication_proxy_and_limits() -> None:
    async def echo(scope, receive, send):  # type: ignore[no-untyped-def]
        message = await receive()
        await server_module._response(send, 200, message.get("body", b"{}"))

    app = HTTPPolicy(echo, "token", max_body=4, timeout=1)
    assert await request(app, path="/healthz") == (200, {"status": "ok"})
    assert (await request(app))[0] == 401
    # Forwarded identity cannot bypass direct bearer authentication.
    assert (await request(app, headers=[(b"x-forwarded-user", b"trusted")]))[0] == 401
    auth = (b"authorization", b"Bearer token")
    assert await request(app, headers=[auth], body=b"{}") == (200, {})
    assert (await request(app, headers=[auth, (b"content-length", b"5")]))[0] == 413
    assert (await request(app, headers=[auth, (b"content-length", b"wat")]))[0] == 400
    assert (await request(app, headers=[auth], body=b"12345"))[0] == 413


@pytest.mark.asyncio
async def test_http_timeout() -> None:
    async def slow(scope, receive, send):  # type: ignore[no-untyped-def]
        await asyncio.sleep(1)

    status, body = await request(
        HTTPPolicy(slow, "token", 10, 0.001), headers=[(b"authorization", b"Bearer token")]
    )
    assert (status, body) == (504, {"error": "request timeout"})


@pytest.mark.asyncio
async def test_http_rate_limit_does_not_trust_forwarded_identity() -> None:
    async def ok(scope, receive, send):  # type: ignore[no-untyped-def]
        await server_module._response(send, 200, b"{}")

    app = HTTPPolicy(ok, "token", 10, 1, rate_limit=1)
    auth = (b"authorization", b"Bearer token")
    assert (await request(app, headers=[auth, (b"x-forwarded-for", b"one")]))[0] == 200
    assert (await request(app, headers=[auth, (b"x-forwarded-for", b"two")]))[0] == 429


@pytest.mark.asyncio
async def test_every_advertised_capability_and_tool_response(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("needle", encoding="utf-8")
    server = create_server(Workspace([tmp_path]))
    tools = await server.list_tools()
    assert {tool.name for tool in tools} == {"inspect_path", "scan_text", "observe_changes"}
    assert await server.list_resources() == []
    assert await server.list_resource_templates() == []
    assert await server.list_prompts() == []
    result = await server.call_tool("inspect_path", {"path": str(tmp_path / "file.txt")})
    assert result[1]["kind"] == "file"


@pytest.mark.asyncio
async def test_tool_failure_timeout_and_malformed_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = Workspace([tmp_path])
    server = create_server(workspace)
    with pytest.raises(Exception, match="OUTSIDE_ROOT"):
        await server.call_tool("inspect_path", {"path": str(tmp_path.parent)})
    with pytest.raises(Exception, match="validation|path|extra"):
        await server.call_tool("inspect_path", {"path": "", "unknown": True})
    with pytest.raises(Exception, match="validation|path"):
        await server.call_tool("inspect_path", {"path": "x" * 4097})
    with pytest.raises(Exception, match="validation|glob"):
        await server.call_tool("scan_text", {"path": str(tmp_path), "query": "x", "glob": ""})

    async def slow(**kwargs):  # type: ignore[no-untyped-def]
        await asyncio.sleep(0.1)
        return {}

    monkeypatch.setattr(workspace, "inspect_path", slow)
    monkeypatch.setattr(server_module, "TIMEOUT", 0.001)
    timed_server = create_server(workspace)
    with pytest.raises(Exception, match="TIMEOUT"):
        await timed_server.call_tool("inspect_path", {"path": str(tmp_path)})
