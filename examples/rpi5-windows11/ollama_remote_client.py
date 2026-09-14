"""Minimal supervised Ollama client for an AISLOP server on another machine."""

from __future__ import annotations

import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from ollama import AsyncClient


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


def result_text(result: object) -> str:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return json.dumps(structured, default=str)
    return "\n".join(getattr(item, "text", str(item)) for item in result.content)


async def main() -> None:
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
            tools = [ollama_tool(tool) for tool in (await session.list_tools()).tools]
            print(f"Connected to {url}; discovered {len(tools)} tools.")

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
