from pathlib import Path

import pytest

from scripts.validate_release_artifacts import (
    EXPECTED_PYTHON,
    _python_requirements_match,
    validate_project_configuration,
)


def test_project_python_requirement_matches_release_policy() -> None:
    validate_project_configuration()


def test_python_requirement_clause_order_does_not_affect_validation() -> None:
    assert _python_requirements_match("<3.14,>=3.12")


def test_project_python_requirement_mismatch_is_actionable(tmp_path: Path) -> None:
    project_file = tmp_path / "pyproject.toml"
    project_file.write_text('[project]\nrequires-python = ">=3.11"\n', encoding="utf-8")

    with pytest.raises(ValueError, match=rf"expected {EXPECTED_PYTHON!r}"):
        validate_project_configuration(project_file)
