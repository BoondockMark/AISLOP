"""Fail CI when the reviewed production lock is incomplete or uses unsafe sources."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
requirements = (ROOT / "requirements.lock").read_text(encoding="utf-8")
pins = [
    line.strip() for line in requirements.splitlines() if line.strip() and not line.startswith("#")
]

if len(pins) < 2:
    raise SystemExit("requirements.lock must include the transitive production graph")
if any(" @ " in pin or "://" in pin or pin.startswith(("-e", "--")) for pin in pins):
    raise SystemExit("requirements.lock may contain only reviewed index packages")
if any("==" not in pin for pin in pins):
    raise SystemExit("every production package must have an exact version pin")

declared = next(item for item in project["dependencies"] if item.startswith("mcp[cli]"))
match = next(
    (re.fullmatch(r"mcp\[cli\]==([^\s;]+)\s*", pin) for pin in pins if pin.startswith("mcp[cli]")),
    None,
)
if match is None:
    raise SystemExit("requirements.lock must contain one exact mcp[cli] pin")

major, minor, patch = (int(part) for part in match.group(1).split("."))
if not ((major, minor, patch) >= (1, 30, 0) and major < 2):
    raise SystemExit(f"locked {match.group(0)!r} is outside {declared!r}")

print(f"validated {len(pins)} reviewed production pins; {match.group(0)} satisfies {declared}")
