from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_systemd_entry_point_matches_packaged_rf_command() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
    rf_commands = {
        name
        for name, target in metadata["project"]["scripts"].items()
        if target.startswith("rf_mcp.")
    }
    unit = (ROOT / "systemd" / "SDR-MCP.service").read_text()

    assert rf_commands == {"rf-mcp"}
    assert 'ExecStart="__RF_MCP_PROJECT_DIR__/.venv/bin/rf-mcp"' in unit


def _write_executable(path: Path, contents: str) -> None:
    path.write_text(contents)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_installer_uses_installed_console_script_in_generated_unit(tmp_path: Path) -> None:
    project = tmp_path / "checked-out-somewhere-else"
    (project / "scripts").mkdir(parents=True)
    (project / "systemd").mkdir()
    shutil.copy2(ROOT / "scripts" / "install-service.sh", project / "scripts")
    shutil.copy2(ROOT / "systemd" / "SDR-MCP.service", project / "systemd")

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    call_log = tmp_path / "calls"
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()

    _write_executable(
        fake_bin / "python3",
        """#!/usr/bin/env bash
set -eu
if [[ "$1" == "-c" ]]; then exit 0; fi
if [[ "$1" == "-m" && "$2" == "venv" ]]; then
  mkdir -p "$3/bin"
  cp "$0" "$3/bin/python"
  exit 0
fi
if [[ "$1" == "-m" && "$2" == "pip" && "$3" == "install" ]]; then
  printf '#!/usr/bin/env bash\\nexit 0\\n' > "$(dirname "$0")/rf-mcp"
  chmod +x "$(dirname "$0")/rf-mcp"
  exit 0
fi
exit 99
""",
    )
    _write_executable(
        fake_bin / "sudo",
        """#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >> "$CALL_LOG"
exec "$@"
""",
    )
    _write_executable(
        fake_bin / "systemctl",
        """#!/usr/bin/env bash
set -eu
printf 'systemctl %s\\n' "$*" >> "$CALL_LOG"
""",
    )

    env = os.environ | {
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "PYTHON_BIN": str(fake_bin / "python3"),
        "SYSTEMD_UNIT_DIR": str(unit_dir),
        "CALL_LOG": str(call_log),
        "USER": os.environ.get("USER", "root"),
    }
    completed = subprocess.run(
        [project / "scripts" / "install-service.sh"],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    executable = project / ".venv" / "bin" / "rf-mcp"
    generated_unit = (unit_dir / "SDR-MCP.service").read_text()
    assert executable.is_file()
    assert f'WorkingDirectory="{project}"' in generated_unit
    assert f'ExecStart="{executable}"' in generated_unit
    assert "SDR-MCP.service" in call_log.read_text()
    assert "RF MCP is listening on TCP port 8765." in completed.stdout
    assert ":8765/dashboard" in completed.stdout
    assert "without it connects" in completed.stdout
