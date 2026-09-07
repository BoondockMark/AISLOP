import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from aislop import core
from aislop.core import AISLOPError, Workspace


def run(awaitable):  # type: ignore[no-untyped-def]
    return asyncio.run(awaitable)


def test_inspect_directory_metadata_content_and_limits(tmp_path: Path) -> None:
    (tmp_path / "b").write_text("b", encoding="utf-8")
    (tmp_path / "a").write_text("abcdef", encoding="utf-8")
    workspace = Workspace([tmp_path])
    directory = run(workspace.inspect_path(str(tmp_path), max_entries=1))
    content = run(workspace.inspect_path(str(tmp_path / "a"), True, max_bytes=3))
    assert directory["entries"] == ["a"] and directory["truncated"] is True
    assert content["kind"] == "file" and content["content"] == "abc"
    assert content["truncated"] is True and content["modified_at"].endswith("+00:00")


def test_inspect_rejects_missing_outside_and_non_utf8(tmp_path: Path) -> None:
    workspace = Workspace([tmp_path])
    (tmp_path / "binary").write_bytes(b"\xff")
    for path, code in [(tmp_path / "missing", "NOT_FOUND"), (tmp_path.parent, "OUTSIDE_ROOT")]:
        with pytest.raises(AISLOPError) as caught:
            run(workspace.inspect_path(str(path)))
        assert caught.value.payload["code"] == code
    with pytest.raises(AISLOPError) as caught:
        run(workspace.inspect_path(str(tmp_path / "binary"), True))
    assert caught.value.payload["code"] == "NOT_TEXT"


def test_scan_literal_regex_case_glob_and_binary_skip(tmp_path: Path) -> None:
    (tmp_path / "one.txt").write_text("Alpha\nalpha two\n", encoding="utf-8")
    (tmp_path / "ignored.log").write_text("alpha", encoding="utf-8")
    (tmp_path / "binary.txt").write_bytes(b"\xffalpha")
    workspace = Workspace([tmp_path])
    literal = run(workspace.scan_text(str(tmp_path), "ALPHA", case_sensitive=False, glob="*.txt"))
    regex = run(workspace.scan_text(str(tmp_path), r"two$", mode="regex"))
    assert [(m["line"], m["column"]) for m in literal["matches"]] == [(1, 1), (2, 1)]
    assert regex["matches"][0]["text"] == "alpha two"


def test_observe_reports_every_change_and_consumes_cursor(tmp_path: Path) -> None:
    old = tmp_path / "old"
    changed = tmp_path / "changed"
    old.write_text("old", encoding="utf-8")
    changed.write_text("before", encoding="utf-8")
    workspace = Workspace([tmp_path])
    baseline = run(workspace.observe_changes(str(tmp_path)))
    old.unlink()
    changed.write_text("longer-after", encoding="utf-8")
    created = tmp_path / "created"
    created.write_text("new", encoding="utf-8")
    result = run(workspace.observe_changes(str(tmp_path), baseline["cursor"], max_changes=2))
    assert result["truncated"] is True
    assert {entry["type"] for entry in result["changes"]}.issubset(
        {"created", "modified", "deleted"}
    )
    with pytest.raises(AISLOPError, match="cursor") as caught:
        run(workspace.observe_changes(str(tmp_path), baseline["cursor"]))
    assert caught.value.payload["code"] == "CURSOR_EXPIRED"


def test_permission_denial_is_a_safe_domain_error(tmp_path: Path) -> None:
    target = tmp_path / "private"
    target.write_text("secret", encoding="utf-8")
    workspace = Workspace([tmp_path])
    with patch.object(Path, "lstat", side_effect=PermissionError("denied")):
        with pytest.raises(AISLOPError) as caught:
            run(workspace.inspect_path(str(target)))
    assert caught.value.payload == {
        "code": "NOT_READABLE",
        "message": "path is not readable",
        "retryable": False,
        "path": str(target),
    }


def test_traversal_limit_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "one").write_text("x", encoding="utf-8")
    monkeypatch.setattr(core, "FILE_LIMIT", 0)
    with pytest.raises(AISLOPError) as caught:
        run(Workspace([tmp_path]).scan_text(str(tmp_path), "x"))
    assert caught.value.payload["code"] == "LIMIT_EXCEEDED"


def test_cursor_cache_cleanup(tmp_path: Path) -> None:
    workspace = Workspace([tmp_path])
    for _ in range(260):
        run(workspace.observe_changes(str(tmp_path)))
    assert len(workspace.snapshots) == 256
