import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

CLIENT_PATH = (
    Path(__file__).parents[1] / "examples" / "rpi5-windows11" / "ollama_remote_client.py"
)
SPEC = importlib.util.spec_from_file_location("ollama_remote_client", CLIENT_PATH)
assert SPEC and SPEC.loader
CLIENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT)


def test_load_environment_reads_dotenv_without_overwriting_process_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Local settings\n"
        "RF_MCP_URL=http://pi.local:8765/mcp\n"
        "RF_MCP_API_TOKEN=token=with=equals\n"
        "OLLAMA_MODEL=from-file\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("RF_MCP_URL", raising=False)
    monkeypatch.delenv("RF_MCP_API_TOKEN", raising=False)
    monkeypatch.setenv("OLLAMA_MODEL", "from-process")

    CLIENT.load_environment(env_file)

    assert os.environ["RF_MCP_URL"] == "http://pi.local:8765/mcp"
    assert os.environ["RF_MCP_API_TOKEN"] == "token=with=equals"
    assert os.environ["OLLAMA_MODEL"] == "from-process"


def test_load_environment_rejects_malformed_entry(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("NOT_AN_ASSIGNMENT\n", encoding="utf-8")

    with pytest.raises(SystemExit, match=r"Invalid \.env entry .*:1"):
        CLIENT.load_environment(env_file)


def test_essential_tool_profile_has_exactly_twenty_unique_tools() -> None:
    assert len(CLIENT.ESSENTIAL_TOOL_NAMES) == 20


def test_select_essential_tools_filters_and_sorts_discovered_tools() -> None:
    discovered = [
        SimpleNamespace(name=name)
        for name in reversed([*CLIENT.ESSENTIAL_TOOL_NAMES, "delete_rf_schedule"])
    ]

    selected = CLIENT.select_essential_tools(discovered)

    assert [tool.name for tool in selected] == sorted(CLIENT.ESSENTIAL_TOOL_NAMES)


def test_select_essential_tools_reports_api_mismatch() -> None:
    with pytest.raises(RuntimeError, match="missing essential tools: get_server_health"):
        CLIENT.select_essential_tools(
            [
                SimpleNamespace(name=name)
                for name in CLIENT.ESSENTIAL_TOOL_NAMES
                if name != "get_server_health"
            ]
        )


def test_require_allowed_tool_blocks_fabricated_call() -> None:
    CLIENT.require_allowed_tool("inspect_spectrum")

    with pytest.raises(RuntimeError, match="non-allowlisted tool: delete_rf_schedule"):
        CLIENT.require_allowed_tool("delete_rf_schedule")
