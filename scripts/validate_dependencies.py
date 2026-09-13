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


def normalized_name(requirement: str) -> str:
    """Return the PEP 503 project name, ignoring extras and version constraints."""
    name = re.split(r"[<>=!~;\s\[]", requirement, maxsplit=1)[0]
    return re.sub(r"[-_.]+", "-", name).lower()


def version_parts(version: str) -> tuple[int, ...]:
    match = re.fullmatch(r"(\d+(?:\.\d+)*)(?:[a-zA-Z0-9.+-]*)", version)
    if match is None:
        raise SystemExit(f"unsupported locked version format: {version!r}")
    return tuple(int(part) for part in match.group(1).split("."))


def satisfies(version: str, constraint: str) -> bool:
    actual = version_parts(version)
    constraints = re.findall(r"(>=|<=|==|!=|~=|>|<)\s*([^,;\s]+)", constraint)
    for operator, expected_text in constraints:
        expected = version_parts(expected_text)
        width = max(len(actual), len(expected))
        left = actual + (0,) * (width - len(actual))
        right = expected + (0,) * (width - len(expected))
        if operator == ">=" and not left >= right:
            return False
        if operator == "<=" and not left <= right:
            return False
        if operator == ">" and not left > right:
            return False
        if operator == "<" and not left < right:
            return False
        if operator == "==" and not left == right:
            return False
        if operator == "!=" and not left != right:
            return False
        if operator == "~=":
            upper = (
                (expected[0] + 1,) if len(expected) == 1 else expected[:-2] + (expected[-2] + 1,)
            )
            if not (left >= right and actual[: len(upper)] < upper):
                return False
    return True


locked = {}
for pin in pins:
    requirement = pin.split(";", 1)[0].strip()
    match = re.fullmatch(r"([^=\s]+)==([^\s]+)", requirement)
    if match:
        locked[normalized_name(match.group(1))] = (match.group(2), pin)

validated = []
for declared in project["dependencies"]:
    name = normalized_name(declared)
    if name not in locked:
        raise SystemExit(f"requirements.lock is missing direct production dependency {declared!r}")
    version, pin = locked[name]
    if not satisfies(version, declared):
        raise SystemExit(f"locked {pin!r} is outside {declared!r}")
    validated.append(f"{name}=={version}")

print(
    f"validated {len(pins)} reviewed production pins and all "
    f"{len(validated)} direct dependencies: {', '.join(validated)}"
)
