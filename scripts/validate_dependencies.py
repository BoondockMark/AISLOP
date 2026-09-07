"""Fail CI when the reviewed production pin drifts from the project constraint."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
requirements = (ROOT / "requirements.lock").read_text(encoding="utf-8")

declared = next(item for item in project["dependencies"] if item.startswith("mcp[cli]"))
match = re.fullmatch(r"mcp\[cli\]==([^\s]+)\s*", requirements.splitlines()[-1])
if match is None:
    raise SystemExit("requirements.lock must contain one exact mcp[cli] pin")

major, minor, patch = (int(part) for part in match.group(1).split("."))
if not ((major, minor, patch) >= (1, 13, 1) and major < 2):
    raise SystemExit(f"locked {match.group(0)!r} is outside {declared!r}")

print(f"validated production dependency: {match.group(0)} satisfies {declared}")
