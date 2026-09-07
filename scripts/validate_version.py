"""Ensure a release tag, source version, and built metadata agree."""

from __future__ import annotations

import argparse
import re
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

from aislop import __version__

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def distribution_version(version: str) -> str:
    """Return the PEP 440 spelling used in Python package metadata."""
    return re.sub(r"-(a|alpha|b|beta|rc)\.(\d+)$", r"\1\2", version)


def metadata_version(path: Path) -> str:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            name = next(item for item in archive.namelist() if item.endswith(".dist-info/METADATA"))
            data = archive.read(name)
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            name = next(item for item in archive.getnames() if item.endswith("/PKG-INFO"))
            member = archive.extractfile(name)
            if member is None:
                raise ValueError(f"cannot read {name}")
            data = member.read()
    else:
        raise ValueError(f"unsupported artifact: {path}")
    return str(BytesParser().parsebytes(data)["Version"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="release tag, including the v prefix")
    parser.add_argument("artifacts", nargs="*", type=Path)
    args = parser.parse_args()

    if not SEMVER.fullmatch(__version__):
        raise SystemExit(f"source version is not SemVer: {__version__}")
    if args.tag and args.tag != f"v{__version__}":
        raise SystemExit(f"tag {args.tag!r} does not match source version v{__version__}")
    for artifact in args.artifacts:
        if metadata_version(artifact) != distribution_version(__version__):
            raise SystemExit(f"{artifact} metadata does not match source version {__version__}")


if __name__ == "__main__":
    main()
