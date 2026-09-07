"""Verify that built distributions consistently carry AISLOP's license."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

EXPECTED_LICENSE = "MIT"


def _wheel_members(path: Path) -> tuple[list[str], bytes]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        return names, archive.read(metadata_name)


def _sdist_members(path: Path) -> tuple[list[str], bytes]:
    with tarfile.open(path, "r:gz") as archive:
        names = archive.getnames()
        metadata_name = next(name for name in names if name.endswith("/PKG-INFO"))
        metadata = archive.extractfile(metadata_name)
        if metadata is None:
            raise ValueError(f"cannot read {metadata_name} from {path}")
        return names, metadata.read()


def validate(path: Path) -> None:
    if path.suffix == ".whl":
        names, metadata_bytes = _wheel_members(path)
        has_license = any(name.endswith(".dist-info/licenses/LICENSE") for name in names)
    elif path.name.endswith(".tar.gz"):
        names, metadata_bytes = _sdist_members(path)
        has_license = any(name.endswith("/LICENSE") for name in names)
    else:
        raise ValueError(f"unsupported artifact: {path}")

    metadata = BytesParser().parsebytes(metadata_bytes)
    if metadata["License-Expression"] != EXPECTED_LICENSE:
        raise ValueError(f"{path} does not declare {EXPECTED_LICENSE}")
    if not has_license:
        raise ValueError(f"{path} does not contain LICENSE")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    for artifact in args.artifacts:
        validate(artifact)


if __name__ == "__main__":
    main()
