"""Verify that built distributions contain complete, publishable metadata."""

from __future__ import annotations

import argparse
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path

EXPECTED_LICENSE = "MIT"
EXPECTED_NAME = "aislop-sdr"
EXPECTED_PYTHON = ">=3.12,<3.14"
EXPECTED_SCRIPT = "aislop = aislop.server:main"
PROJECT_FILE = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _python_requirement_clauses(requirement: str) -> frozenset[str]:
    """Return clauses independently of the order used by metadata serializers."""
    return frozenset(clause.strip() for clause in requirement.split(","))


def _python_requirements_match(actual: str, expected: str = EXPECTED_PYTHON) -> bool:
    return _python_requirement_clauses(actual) == _python_requirement_clauses(expected)


def validate_project_configuration(path: Path = PROJECT_FILE) -> None:
    """Ensure source metadata and the release policy cannot silently diverge."""
    with path.open("rb") as project_file:
        requires_python = tomllib.load(project_file)["project"]["requires-python"]
    if not _python_requirements_match(requires_python):
        raise ValueError(
            f"{path} has unexpected Python requirement {requires_python!r}; "
            f"expected {EXPECTED_PYTHON!r}"
        )


def _wheel_members(path: Path) -> tuple[list[str], bytes, bytes]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        scripts_name = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
        return names, archive.read(metadata_name), archive.read(scripts_name)


def _sdist_members(path: Path) -> tuple[list[str], bytes, bytes | None]:
    with tarfile.open(path, "r:gz") as archive:
        names = archive.getnames()
        metadata_name = next(name for name in names if name.endswith("/PKG-INFO"))
        metadata = archive.extractfile(metadata_name)
        if metadata is None:
            raise ValueError(f"cannot read {metadata_name} from {path}")
        return names, metadata.read(), None


def validate(path: Path) -> None:
    if path.suffix == ".whl":
        names, metadata_bytes, entry_points = _wheel_members(path)
        has_license = any(name.endswith(".dist-info/licenses/LICENSE") for name in names)
        required_members = ("aislop/__init__.py", "aislop/py.typed", "aislop/server.py")
        missing = [member for member in required_members if member not in names]
        if missing:
            raise ValueError(f"{path} is missing wheel members: {', '.join(missing)}")
        if EXPECTED_SCRIPT not in entry_points.decode("utf-8").splitlines():
            raise ValueError(f"{path} does not define the {EXPECTED_NAME} console script")
    elif path.name.endswith(".tar.gz"):
        names, metadata_bytes, _ = _sdist_members(path)
        has_license = any(name.endswith("/LICENSE") for name in names)
        for filename in ("README.md", "pyproject.toml", "src/aislop/py.typed"):
            if not any(name.endswith(f"/{filename}") for name in names):
                raise ValueError(f"{path} does not contain {filename}")
    else:
        raise ValueError(f"unsupported artifact: {path}")

    metadata = BytesParser().parsebytes(metadata_bytes)
    if metadata["Name"] != EXPECTED_NAME:
        raise ValueError(f"{path} has unexpected project name {metadata['Name']!r}")
    if metadata["License-Expression"] != EXPECTED_LICENSE:
        raise ValueError(f"{path} does not declare {EXPECTED_LICENSE}")
    if not _python_requirements_match(metadata["Requires-Python"]):
        raise ValueError(
            f"{path} has unexpected Python requirement {metadata['Requires-Python']!r}; "
            f"expected {EXPECTED_PYTHON!r}"
        )
    description = metadata.get_payload()
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"{path} does not contain the README description")
    if not has_license:
        raise ValueError(f"{path} does not contain LICENSE")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    validate_project_configuration()
    for artifact in args.artifacts:
        validate(artifact)


if __name__ == "__main__":
    main()
