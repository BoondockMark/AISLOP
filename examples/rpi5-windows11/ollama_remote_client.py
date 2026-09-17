"""Minimal supervised Ollama client for an AISLOP server on another machine."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from ollama import AsyncClient

# Keep the model-facing tool schema small. The remote AISLOP server still
# advertises its complete API, but this supervised client gives Ollama only the
# common discovery, receive, analysis, scan, and result-retrieval operations.
ESSENTIAL_TOOL_NAMES = frozenset(
    {
        "get_rf_api_contract",
        "get_server_health",
        "list_devices",
        "list_digital_decoder_capabilities",
        "list_sstv_decoder_capabilities",
        "inspect_spectrum",
        "analyze_signal",
        "receive_broadcast_fm",
        "decode_digital_signal",
        "decode_sstv",
        "start_band_scan",
        "get_band_scan_status",
        "get_band_scan_results",
        "stop_band_scan",
        "list_rf_jobs",
        "get_rf_job",
        "list_rf_artifacts",
        "get_rf_artifact",
        "get_storage_status",
        "list_fm_stations",
    }
)


def load_environment(path: Path | None = None) -> None:
    """Load the example's dotenv file without replacing explicit settings."""
    env_file = path or Path(__file__).with_name(".env")
    if not env_file.is_file():
        return

    for line_number, line in enumerate(env_file.read_text(encoding="utf-8").splitlines(), 1):
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        name, separator, value = trimmed.partition("=")
        name = name.strip()
        if not separator or not name:
            raise SystemExit(f"Invalid .env entry at {env_file}:{line_number}")
        os.environ.setdefault(name, value.strip())


def required_environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Set {name} before starting the client.")
    return value


def ollama_tool(tool: object) -> dict[str, object]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def select_essential_tools(discovered_tools: list[object]) -> list[object]:
    """Return the curated model-facing tools, failing on a mismatched server API."""
    by_name = {tool.name: tool for tool in discovered_tools}
    missing = ESSENTIAL_TOOL_NAMES - by_name.keys()
    if missing:
        names = ", ".join(sorted(missing))
        raise RuntimeError(f"AISLOP server is missing essential tools: {names}")
    return [by_name[name] for name in sorted(ESSENTIAL_TOOL_NAMES)]


def require_allowed_tool(tool_name: str) -> None:
    """Enforce the allowlist even if a model fabricates an undisclosed tool call."""
    if tool_name not in ESSENTIAL_TOOL_NAMES:
        raise RuntimeError(f"Model requested non-allowlisted tool: {tool_name}")


def result_text(result: object) -> str:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return json.dumps(structured, default=str)
    return "\n".join(getattr(item, "text", str(item)) for item in result.content)


async def main() -> None:
    load_environment()
    url = required_environment("RF_MCP_URL")
    token = required_environment("RF_MCP_API_TOKEN")
    model = required_environment("OLLAMA_MODEL")
    if not url.endswith("/mcp"):
        raise SystemExit("RF_MCP_URL must include the /mcp endpoint.")

    headers = {"Authorization": f"Bearer {token}"}
    messages = [
        {
            "role": "system",
            "content": (
                "Use RF tools when needed. Begin with get_rf_api_contract. Ask the "
                "user for confirmation before tuning, recording, scheduling, or "
                "performing any other consequential operation."
            ),
        }
    ]
    ollama = AsyncClient()

    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            discovered_tools = (await session.list_tools()).tools
            selected_tools = select_essential_tools(discovered_tools)
            tools = [ollama_tool(tool) for tool in selected_tools]
            print(
                f"Connected to {url}; discovered {len(discovered_tools)} tools and "
                f"exposed {len(tools)} essential tools to Ollama."
            )

            while prompt := (await asyncio.to_thread(input, "you> ")).strip():
                messages.append({"role": "user", "content": prompt})
                while True:
                    response = await ollama.chat(model=model, messages=messages, tools=tools)
                    messages.append(response.message)
                    calls = response.message.tool_calls or []
                    if not calls:
                        print(f"assistant> {response.message.content}")
                        break

                    for call in calls:
                        require_allowed_tool(call.function.name)
                        result = await session.call_tool(
                            call.function.name, call.function.arguments
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_name": call.function.name,
                                "content": result_text(result),
                            }
                        )


if __name__ == "__main__":
    asyncio.run(main())
