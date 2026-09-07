import importlib.metadata
import subprocess
import sys

import aislop
from scripts.validate_version import distribution_version


def test_package_and_cli_use_the_authoritative_version() -> None:
    assert importlib.metadata.version("aislop") == aislop.__version__
    completed = subprocess.run(
        [sys.executable, "-m", "aislop.server", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == f"aislop {aislop.__version__}"


def test_semver_candidate_has_deterministic_python_registry_spelling() -> None:
    assert distribution_version("0.1.0-rc.1") == "0.1.0rc1"
