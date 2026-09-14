# Connect AISLOP to ChatGPT and Ollama

This guide assumes that `aislop-sdr` is installed and that `rf-mcp --version`
works. AISLOP exposes the radio application through either Streamable HTTP or
stdio. Use `rf-mcp`, not the unrelated legacy `aislop` executable.

Before giving either client access to a real receiver, remember that MCP tools
can tune hardware, create recordings and other artifacts, and schedule work.
Review tool calls, run the server as an unprivileged user, and use a dedicated
data directory.

## ChatGPT

ChatGPT connects to a **remote Streamable HTTP** MCP server. It cannot start the
local stdio process, and `127.0.0.1` on the AISLOP machine is not reachable from
the ChatGPT service. The server therefore needs an HTTPS URL that ChatGPT can
reach. Consult OpenAI's current [developer mode
instructions](https://platform.openai.com/docs/guides/developer-mode) and
[MCP guide](https://platform.openai.com/docs/mcp) because plan, workspace, and
administrator availability can change.

### 1. Start and protect AISLOP

Generate a token containing at least 32 supported characters, start the HTTP
transport on a private listener, and confirm readiness:

```sh
export RF_MCP_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export RF_MCP_TRANSPORT=streamable-http
export RF_MCP_HOST=127.0.0.1
export RF_MCP_PORT=8765
export RF_MCP_DATA_DIR="$HOME/SDR-MCP-data"
rf-mcp
```

In a second terminal:

```sh
curl --fail http://127.0.0.1:8765/healthz
```

Put a TLS reverse proxy or a secure tunnel in front of that listener. It must
forward requests to `http://127.0.0.1:8765` without removing MCP session headers
or the `Authorization` header. The resulting endpoint should look like:

```text
https://rf.example.net/mcp
```

Do not expose port 8765 directly to the Internet, publish an unauthenticated
server, or place the token in a URL query string. AISLOP supplies bearer-token
authentication but does not terminate TLS or provide per-user authorization.

### 2. Add the connector in ChatGPT

The exact labels depend on the current ChatGPT plan and workspace policy:

1. In **Settings**, open **Apps & Connectors** (called **Connectors** in some
   interfaces), open **Advanced settings**, and enable **Developer mode**. A
   workspace administrator may need to allow it first.
2. Choose **Create** or **Add custom connector**.
3. Give it a name such as `AISLOP RF Lab` and enter the complete MCP URL,
   including `/mcp`: `https://rf.example.net/mcp`.
4. Select the authentication option that allows a bearer token/static header
   and supply `Authorization: Bearer <RF_MCP_API_TOKEN>`. If the ChatGPT form
   offered to your account supports only no authentication or OAuth, do **not**
   make AISLOP public; instead place an OAuth-capable MCP gateway in front of
   AISLOP and have the gateway add the bearer header upstream.
5. Save the connector and allow ChatGPT to discover its tools.

Start a new chat, enable/select the connector from the tools or **+** menu, and
begin with read-only discovery:

```text
Use the AISLOP RF Lab connector. Call get_rf_api_contract, then summarize the
available receiver backends and decoder capabilities. Do not tune, record,
schedule, or otherwise mutate anything without asking me first.
```

Keep tool-call confirmation enabled for consequential actions. If discovery
fails, verify the public HTTPS URL from a network outside the server, ensure the
URL ends in `/mcp`, inspect reverse-proxy logs, and confirm that the proxy passes
the bearer and MCP session headers. `/healthz` being healthy proves that the
process is ready; it does not prove that ChatGPT can reach or authenticate to
`/mcp`.

## Ollama

Ollama models can request tools, but the Ollama server is not itself an MCP
host. A small client must connect to AISLOP, translate its discovered MCP tools
to Ollama tool definitions, execute requested calls through MCP, and return the
results to the model. The example below does that locally with stdio, so no
listener, TLS, or API token is needed. See Ollama's current [tool-calling
documentation](https://docs.ollama.com/capabilities/tool-calling) for compatible
models and API behavior.

### 1. Prepare Ollama and the Python client

Start Ollama, fetch a model that supports tool calling, and install the Ollama
Python package in the same virtual environment as AISLOP:

```sh
ollama serve
ollama pull <tool-capable-model>
. .venv/bin/activate
python -m pip install ollama
```

Save the following as `ollama_rf_mcp.py`. Replace the executable and data paths
with absolute paths; this is especially important when the script is launched
by a GUI or service that has a limited `PATH`.

```python
import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ollama import AsyncClient

MODEL = "<tool-capable-model>"
SERVER = StdioServerParameters(
    command="/absolute/path/to/AISLOP/.venv/bin/rf-mcp",
    args=[],
    env={
        "RF_MCP_TRANSPORT": "stdio",
        "RF_MCP_DATA_DIR": "/absolute/writable/path/SDR-MCP-data",
    },
)


def ollama_tool(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def result_text(result):
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return json.dumps(structured, default=str)
    return "\n".join(
        getattr(item, "text", str(item)) for item in result.content
    )


async def main():
    messages = [{
        "role": "system",
        "content": (
            "Use RF tools when needed. Begin with get_rf_api_contract. "
            "Ask for confirmation before tuning, recording, scheduling, "
            "or any other consequential operation."
        ),
    }]

    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [ollama_tool(tool) for tool in (await session.list_tools()).tools]

            while prompt := input("you> ").strip():
                messages.append({"role": "user", "content": prompt})
                while True:
                    response = await AsyncClient().chat(
                        model=MODEL, messages=messages, tools=tools
                    )
                    messages.append(response.message)
                    calls = response.message.tool_calls or []
                    if not calls:
                        print(f"assistant> {response.message.content}")
                        break

                    for call in calls:
                        result = await session.call_tool(
                            call.function.name, call.function.arguments
                        )
                        messages.append({
                            "role": "tool",
                            "tool_name": call.function.name,
                            "content": result_text(result),
                        })


if __name__ == "__main__":
    asyncio.run(main())
```

Run it with:

```sh
python ollama_rf_mcp.py
```

Then enter a conservative first request such as:

```text
Inspect the RF API contract and list receiver backends. Do not change receiver
state or create artifacts.
```

This demonstration trusts the model to follow the confirmation instruction;
for unattended or shared deployments, enforce an allowlist in the client and
require application-level approval before forwarding consequential tool calls.
To use a separately hosted AISLOP instance instead, replace `stdio_client` with
the MCP SDK's Streamable HTTP client, use the full `/mcp` URL, and send the
bearer header described in the main README.

## Common problems

| Symptom | Check |
| --- | --- |
| ChatGPT cannot discover tools | Use a publicly reachable HTTPS URL ending in `/mcp`; do not use `localhost`. |
| `401 Unauthorized` | Ensure the client or gateway sends exactly `Authorization: Bearer <token>`. |
| Dashboard works but MCP does not | Test `/mcp`, not `/dashboard`; ensure the proxy preserves streaming and session headers. |
| Ollama never requests a tool | Use a model with tool-calling support and keep the discovered `tools` argument on every model turn. |
| Ollama script cannot start AISLOP | Use an absolute `rf-mcp` path, a writable absolute data path, and `RF_MCP_TRANSPORT=stdio`. |
| Radio or decoder tool is unavailable | Verify the receiver utilities, drivers, permissions, antenna, and optional decoder dependencies described in the README. |
