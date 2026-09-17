import zipfile
from pathlib import Path

import pytest

from scripts.validate_release_artifacts import (
    EXPECTED_PYTHON,
    EXPECTED_SCRIPTS,
    REQUIRED_DASHBOARD_ASSETS,
    REQUIRED_RF_MODULES,
    _python_requirements_match,
    validate,
    validate_project_configuration,
)


@pytest.fixture
def wheel_members() -> set[str]:
    return {
        "aislop/__init__.py",
        "aislop/py.typed",
        "aislop/server.py",
        *REQUIRED_RF_MODULES,
        *REQUIRED_DASHBOARD_ASSETS,
    }


@pytest.fixture
def wheel_factory(tmp_path: Path):
    def create(members: set[str], scripts: tuple[str, ...] = EXPECTED_SCRIPTS) -> Path:
        wheel = tmp_path / "aislop_sdr-1.0.0-py3-none-any.whl"
        metadata = (
            "Metadata-Version: 2.4\n"
            "Name: aislop-sdr\n"
            "Version: 1.0.0\n"
            "License-Expression: MIT\n"
            f"Requires-Python: {EXPECTED_PYTHON}\n"
            "\n"
            "AISLOP release fixture.\n"
        )
        entry_points = "[console_scripts]\n" + "\n".join(scripts) + "\n"
        with zipfile.ZipFile(wheel, "w") as archive:
            for member in members:
                archive.writestr(member, b"")
            archive.writestr("aislop_sdr-1.0.0.dist-info/METADATA", metadata)
            archive.writestr("aislop_sdr-1.0.0.dist-info/entry_points.txt", entry_points)
            archive.writestr("aislop_sdr-1.0.0.dist-info/licenses/LICENSE", "MIT\n")
        return wheel

    return create


def test_project_python_requirement_matches_release_policy() -> None:
    validate_project_configuration()


def test_python_requirement_clause_order_does_not_affect_validation() -> None:
    assert _python_requirements_match("<3.15,>=3.12")


def test_project_python_requirement_mismatch_is_actionable(tmp_path: Path) -> None:
    project_file = tmp_path / "pyproject.toml"
    project_file.write_text('[project]\nrequires-python = ">=3.11"\n', encoding="utf-8")

    with pytest.raises(ValueError, match=rf"expected {EXPECTED_PYTHON!r}"):
        validate_project_configuration(project_file)


def test_complete_wheel_contains_rf_package_assets_and_scripts(
    wheel_factory, wheel_members: set[str]
) -> None:
    validate(wheel_factory(wheel_members))


@pytest.mark.parametrize(
    "missing_member",
    (REQUIRED_RF_MODULES[0], *REQUIRED_DASHBOARD_ASSETS),
)
def test_wheel_rejects_missing_rf_modules_or_dashboard_assets(
    wheel_factory, wheel_members: set[str], missing_member: str
) -> None:
    wheel_members.remove(missing_member)

    with pytest.raises(ValueError, match="missing wheel members"):
        validate(wheel_factory(wheel_members))


@pytest.mark.parametrize("missing_script", EXPECTED_SCRIPTS)
def test_wheel_rejects_missing_supported_console_entry_point(
    wheel_factory, wheel_members: set[str], missing_script: str
) -> None:
    scripts = tuple(script for script in EXPECTED_SCRIPTS if script != missing_script)

    with pytest.raises(ValueError, match="does not define console scripts"):
        validate(wheel_factory(wheel_members, scripts))
