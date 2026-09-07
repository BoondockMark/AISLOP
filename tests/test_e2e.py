import json
import os
import shutil
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_packaged_executable_initialization_discovery_and_calls(tmp_path: Path) -> None:
    executable = shutil.which("aislop")
    assert executable, "install the package before running end-to-end tests"
    (tmp_path / "sample.txt").write_text("hello protocol", encoding="utf-8")
    diagnostics = tmp_path / "stderr.log"
    parameters = StdioServerParameters(
        command=executable,
        args=["--allow-root", str(tmp_path)],
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    with diagnostics.open("w+", encoding="utf-8") as stderr:
        async with stdio_client(parameters, errlog=stderr) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                initialized = await session.initialize()
                assert initialized.serverInfo.name == "AISLOP"
                assert {tool.name for tool in (await session.list_tools()).tools} == {
                    "inspect_path",
                    "scan_text",
                    "observe_changes",
                }
                assert (await session.list_resources()).resources == []
                assert (await session.list_resource_templates()).resourceTemplates == []
                assert (await session.list_prompts()).prompts == []
                inspected = await session.call_tool(
                    "inspect_path", {"path": str(tmp_path / "sample.txt"), "include_content": True}
                )
                assert inspected.isError is False
                assert json.loads(inspected.content[0].text)["content"] == "hello protocol"
                scanned = await session.call_tool(
                    "scan_text", {"path": str(tmp_path), "query": "protocol"}
                )
                assert scanned.isError is False
        stderr.seek(0)
        diagnostic_text = stderr.read()
    # Successful parsing by ClientSession proves stdout contained only MCP frames;
    # the SDK's process diagnostics were independently redirected to stderr.
    assert not any(line.startswith("{") for line in diagnostic_text.splitlines())
