import asyncio
from pathlib import Path

import pytest

from aislop.core import AISLOPError, Workspace


def test_inspect_and_scan_are_bounded(tmp_path: Path):
    (tmp_path / "hello.txt").write_text("Hello world\nsecond line\n", encoding="utf-8")
    workspace = Workspace([tmp_path])

    inspected = asyncio.run(workspace.inspect_path(str(tmp_path / "hello.txt"), True, 5))
    assert inspected["content"] == "Hello"
    assert inspected["truncated"] is True

    scanned = asyncio.run(workspace.scan_text(str(tmp_path), "world", max_results=1))
    assert scanned["matches"][0]["column"] == 7
    assert scanned["truncated"] is True


def test_root_escape_and_change_cursor(tmp_path: Path):
    workspace = Workspace([tmp_path])
    with pytest.raises(AISLOPError, match="outside") as caught:
        asyncio.run(workspace.inspect_path(str(tmp_path.parent)))
    assert caught.value.payload["code"] == "OUTSIDE_ROOT"

    baseline = asyncio.run(workspace.observe_changes(str(tmp_path)))
    (tmp_path / "new.txt").write_text("new", encoding="utf-8")
    changed = asyncio.run(workspace.observe_changes(str(tmp_path), baseline["cursor"]))
    assert changed["changes"] == [{"path": str(tmp_path / "new.txt"), "type": "created"}]
    with pytest.raises(AISLOPError) as expired:
        asyncio.run(workspace.observe_changes(str(tmp_path), baseline["cursor"]))
    assert expired.value.payload["code"] == "CURSOR_EXPIRED"


def test_inspect_reports_safe_symlink_without_following_it(tmp_path: Path):
    target = tmp_path / "target.txt"
    target.write_text("secret", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(target)

    inspected = asyncio.run(Workspace([tmp_path]).inspect_path(str(link), include_content=True))

    assert inspected["path"] == str(link)
    assert inspected["kind"] == "symlink"
    assert "content" not in inspected


@pytest.mark.parametrize("query", [r"(a)\1", r"(?=a)", r"(?P<n>a)", r"a++"])
def test_scan_rejects_regex_syntax_not_supported_by_re2(tmp_path: Path, query: str):
    (tmp_path / "input.txt").write_text("aaaa", encoding="utf-8")

    with pytest.raises(AISLOPError) as caught:
        asyncio.run(Workspace([tmp_path]).scan_text(str(tmp_path), query, mode="regex"))

    assert caught.value.payload["code"] == "INVALID_PATTERN"
