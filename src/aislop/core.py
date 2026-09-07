"""Transport-independent AISLOP tool implementation."""

from __future__ import annotations

import asyncio
import fnmatch
import os
import re
import secrets
import stat
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FILE_LIMIT = 10_000
BYTE_LIMIT = 100 * 1024 * 1024


class AISLOPError(Exception):
    """An error safe to expose to an MCP client."""

    def __init__(
        self, code: str, message: str, *, retryable: bool = False, path: str | None = None
    ):
        super().__init__(message)
        self.payload = {"code": code, "message": message, "retryable": retryable}
        if path is not None:
            self.payload["path"] = path


@dataclass(frozen=True)
class Snapshot:
    root: Path
    values: dict[str, tuple[int, int, int]]


class Workspace:
    """Enforces roots and owns process-local observation cursors."""

    def __init__(self, roots: list[Path]):
        self.roots = tuple(root.resolve(strict=True) for root in roots)
        self.snapshots: dict[str, Snapshot] = {}

    def resolve(self, value: str) -> Path:
        # Keep the lexical path for lstat()/reporting so an in-root symlink is
        # observable as a symlink, but authorize its fully resolved target.
        # Authorizing only the lexical path would allow an in-root symlink to
        # escape an allowed root.
        candidate = Path(value).expanduser().absolute()
        resolved = candidate.resolve(strict=False)
        if not any(resolved == root or resolved.is_relative_to(root) for root in self.roots):
            raise AISLOPError("OUTSIDE_ROOT", "path is outside configured roots", path=value)
        if not candidate.exists() and not candidate.is_symlink():
            raise AISLOPError("NOT_FOUND", "path does not exist", path=value)
        return candidate

    @staticmethod
    def display(path: Path) -> str:
        return str(path)

    async def inspect_path(
        self,
        path: str,
        include_content: bool = False,
        max_bytes: int = 65536,
        max_entries: int = 200,
    ) -> dict[str, Any]:
        target = self.resolve(path)
        try:
            info = await asyncio.to_thread(target.lstat)
            kind = (
                "symlink"
                if target.is_symlink()
                else "directory"
                if target.is_dir()
                else "file"
                if target.is_file()
                else "other"
            )
            result: dict[str, Any] = {
                "path": self.display(target),
                "kind": kind,
                "size": info.st_size,
                "modified_at": datetime.fromtimestamp(info.st_mtime, UTC).isoformat(),
                "truncated": False,
            }
            if kind == "directory":
                entries = await asyncio.to_thread(lambda: sorted(p.name for p in target.iterdir()))
                result["truncated"] = len(entries) > max_entries
                result["entries"] = entries[:max_entries]
            elif include_content and kind == "file":
                raw = await asyncio.to_thread(_read_bounded, target, max_bytes)
                result["truncated"] = len(raw) > max_bytes
                try:
                    result["content"] = raw[:max_bytes].decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise AISLOPError(
                        "NOT_TEXT", "file is not valid UTF-8 text", path=path
                    ) from exc
            return result
        except AISLOPError:
            raise
        except PermissionError as exc:
            raise AISLOPError("NOT_READABLE", "path is not readable", path=path) from exc
        except OSError as exc:
            raise AISLOPError("IO_ERROR", str(exc), retryable=True, path=path) from exc

    async def scan_text(
        self,
        path: str,
        query: str,
        mode: str = "literal",
        case_sensitive: bool = True,
        glob: str = "**/*",
        max_results: int = 100,
    ) -> dict[str, Any]:
        target = self.resolve(path)
        try:
            pattern = _compile(query, mode, case_sensitive)
            matches: list[dict[str, Any]] = []
            files_scanned = total_bytes = 0
            for file in _files(target, glob):
                await asyncio.sleep(0)
                files_scanned += 1
                total_bytes += file.stat().st_size
                if files_scanned > FILE_LIMIT or total_bytes > BYTE_LIMIT:
                    raise AISLOPError("LIMIT_EXCEEDED", "scan traversal limit exceeded", path=path)
                try:
                    text = file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for number, line in enumerate(text.splitlines(), 1):
                    found = pattern.search(line)
                    if found:
                        matches.append(
                            {
                                "path": self.display(file),
                                "line": number,
                                "column": found.start() + 1,
                                "text": line,
                            }
                        )
                        if len(matches) >= max_results:
                            return {
                                "matches": matches,
                                "files_scanned": files_scanned,
                                "truncated": True,
                            }
            return {"matches": matches, "files_scanned": files_scanned, "truncated": False}
        except AISLOPError:
            raise
        except PermissionError as exc:
            raise AISLOPError("NOT_READABLE", "path is not readable", path=path) from exc
        except OSError as exc:
            raise AISLOPError("IO_ERROR", str(exc), retryable=True, path=path) from exc

    async def observe_changes(
        self, path: str, cursor: str | None = None, glob: str = "**/*", max_changes: int = 200
    ) -> dict[str, Any]:
        target = self.resolve(path)
        current = await asyncio.to_thread(_snapshot, target, glob)
        old: dict[str, tuple[int, int, int]] = {}
        if cursor is not None:
            saved = self.snapshots.pop(cursor, None)
            if saved is None or saved.root != target:
                raise AISLOPError(
                    "CURSOR_EXPIRED", "cursor is unknown, expired, or belongs to another path"
                )
            old = saved.values
        changes = (
            (
                [{"path": p, "type": "created"} for p in current.keys() - old.keys()]
                + [{"path": p, "type": "deleted"} for p in old.keys() - current.keys()]
                + [
                    {"path": p, "type": "modified"}
                    for p in current.keys() & old.keys()
                    if current[p] != old[p]
                ]
            )
            if cursor
            else []
        )
        changes.sort(key=lambda item: (item["path"], item["type"]))
        new_cursor = secrets.token_urlsafe(24)
        self.snapshots[new_cursor] = Snapshot(target, current)
        while len(self.snapshots) > 256:
            self.snapshots.pop(next(iter(self.snapshots)))
        return {
            "cursor": new_cursor,
            "changes": changes[:max_changes],
            "truncated": len(changes) > max_changes,
        }


def _read_bounded(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        return stream.read(limit + 1)


def _files(target: Path, glob: str):
    if target.is_file():
        yield target
        return
    for base, dirs, names in os.walk(target, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not Path(base, d).is_symlink())
        for name in sorted(names):
            item = Path(base, name)
            relative = item.relative_to(target).as_posix()
            matches_glob = fnmatch.fnmatch(relative, glob)
            if glob.startswith("**/"):
                matches_glob = matches_glob or fnmatch.fnmatch(relative, glob[3:])
            if not item.is_symlink() and matches_glob:
                yield item


def _compile(query: str, mode: str, case_sensitive: bool):
    flags = 0 if case_sensitive else re.IGNORECASE
    if mode == "literal":
        query = re.escape(query)
    else:
        # Python's engine accepts constructs that RE2 deliberately excludes.
        # Reject them before compilation so clients get the promised portable
        # RE2-compatible grammar rather than Python-specific behavior.
        unsupported = (
            r"\\[1-9]",  # numeric backreferences
            r"\\g[<{]",  # explicit backreferences
            r"\(\?P[<=]",  # named groups/backreferences
            r"\(\?(?:<?[=!]|\(|>)",  # lookaround, conditionals, atomic groups
            r"(?:[*+?]|\{\d+(?:,\d*)?\})\+",  # possessive quantifiers
        )
        if any(re.search(fragment, query) for fragment in unsupported):
            raise AISLOPError("INVALID_PATTERN", "pattern uses syntax unsupported by RE2")
    try:
        return re.compile(query, flags)
    except re.error as exc:
        raise AISLOPError("INVALID_PATTERN", str(exc)) from exc


def _snapshot(target: Path, glob: str) -> dict[str, tuple[int, int, int]]:
    values: dict[str, tuple[int, int, int]] = {}
    candidates = [target] if target.is_file() else list(_files(target, glob))
    if len(candidates) > FILE_LIMIT:
        raise AISLOPError("LIMIT_EXCEEDED", "observation path limit exceeded", path=str(target))
    for item in candidates:
        info = item.stat()
        values[str(item)] = (info.st_mtime_ns, info.st_size, stat.S_IFMT(info.st_mode))
    return values
