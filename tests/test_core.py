from pathlib import Path
import asyncio

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
