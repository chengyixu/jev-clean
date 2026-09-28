"""Streaming filesystem metadata, no file-count/time caps, no content reads.

Native elevation uses fixed find/stat argv, never a privileged Python interpreter.
"""

from __future__ import annotations

import glob
import os
import re
import selectors
import stat
import subprocess
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable, Iterator


@dataclass(frozen=True)
class FileMeta:
    device: int
    inode: int
    mode: int
    uid: int
    nlink: int
    size: int
    blocks: int
    mtime_ns: int
    ctime_ns: int

    @classmethod
    def from_stat(cls, s: os.stat_result):
        return cls(
            s.st_dev,
            s.st_ino,
            s.st_mode,
            s.st_uid,
            s.st_nlink,
            s.st_size,
            s.st_blocks,
            s.st_mtime_ns,
            s.st_ctime_ns,
        )


@dataclass(frozen=True)
class WalkEntry:
    path: Path
    metadata: FileMeta


STAT_FORMAT = "%@:%d:%i:%p:%u:%l:%z:%b:%.9Fm:%.9Fc"


def excluded(path: Path, exclusions: list[Path]) -> bool:
    return any(path == root or path.is_relative_to(root) for root in exclusions)


def walk_user(
    root: Path,
    *,
    exclusions: list[Path],
    issue: Callable[[str, str], None],
    directory: Callable[[FileMeta], bool],
    cancelled: Callable[[], bool],
) -> Iterator[WalkEntry]:
    try:
        first = FileMeta.from_stat(root.lstat())
    except OSError as error:
        issue(str(root), f"unreadable root: {error}")
        return
    if excluded(root, exclusions):
        issue(str(root), "scanner-state exclusion")
        return
    if not stat.S_ISDIR(first.mode):
        if not cancelled():
            yield WalkEntry(root, first)
        return

    def failed(error):
        issue(str(error.filename or root), f"unreadable directory: {error}")

    # fwalk holds directory descriptors and checks identity before descending.
    for current, dirs, files, fd in os.fwalk(root, follow_symlinks=False, onerror=failed):
        if cancelled():
            return
        path = Path(current)
        meta = FileMeta.from_stat(os.fstat(fd))
        if meta.device != first.device:
            dirs[:] = []
            issue(str(path), "filesystem boundary")
            continue
        if not directory(meta):
            dirs[:] = []
            continue
        yield WalkEntry(path, meta)
        for name in list(dirs):
            child = path / name
            try:
                child_meta = FileMeta.from_stat(os.stat(name, dir_fd=fd, follow_symlinks=False))
            except OSError as error:
                dirs.remove(name)
                issue(str(child), f"unreadable metadata: {error}")
                continue
            if excluded(child, exclusions):
                dirs.remove(name)
                issue(str(child), "scanner-state exclusion")
            elif child_meta.device != first.device:
                dirs.remove(name)
                issue(str(child), "filesystem boundary")
            elif stat.S_ISLNK(child_meta.mode):
                dirs.remove(name)
                yield WalkEntry(child, child_meta)
        for name in files:
            if cancelled():
                return
            child = path / name
            if excluded(child, exclusions):
                issue(str(child), "scanner-state exclusion")
                continue
            try:
                child_meta = FileMeta.from_stat(os.stat(name, dir_fd=fd, follow_symlinks=False))
            except OSError as error:
                issue(str(child), f"unreadable metadata: {error}")
                continue
            if child_meta.device != first.device:
                issue(str(child), "filesystem boundary")
                continue
            yield WalkEntry(child, child_meta)


def parse_stat_batch(paths: list[Path], text: str) -> list[WalkEntry]:
    records = []
    seen = set()
    for line in text.splitlines():
        fields = line.split(":")
        if len(fields) != 10:
            raise ValueError("Malformed native metadata record")
        ordinal = int(fields[0]) - 1
        if not 0 <= ordinal < len(paths) or ordinal in seen:
            raise ValueError("Invalid native metadata ordinal")
        seen.add(ordinal)
        dev, ino = int(fields[1]), int(fields[2])
        mode = int(fields[3], 8)
        uid, links, size, blocks = map(int, fields[4:8])
        mtime, ctime = (int(Decimal(v) * 10**9) for v in fields[8:10])
        if min(dev, ino, uid, links, size, blocks) < 0:
            raise ValueError("Negative native metadata")
        records.append(
            WalkEntry(paths[ordinal], FileMeta(dev, ino, mode, uid, links, size, blocks, mtime, ctime))
        )
    return records


def privileged_metadata(paths: list[Path], issue, cancelled) -> list[WalkEntry]:
    if not paths or cancelled():
        return []
    if any(not p.is_absolute() or ".." in p.parts for p in paths):
        raise ValueError("Invalid observed path")
    # Exact unprivileged lstat whenever accessible; privileged batches only fill the gaps.
    if len(paths) > 64:
        return [
            entry
            for offset in range(0, len(paths), 64)
            for entry in privileged_metadata(paths[offset : offset + 64], issue, cancelled)
        ]
    accessible = []
    blocked = []
    for path in paths:
        try:
            accessible.append(WalkEntry(path, FileMeta.from_stat(path.lstat())))
        except OSError:
            blocked.append(path)
    if not blocked:
        return accessible
    from jev_clean.infrastructure.native import run

    paths = blocked
    command = ["/usr/bin/sudo", "-n", "/usr/bin/stat", "-f", STAT_FORMAT, *map(str, paths)]
    code, out, err = run(command, 30)
    records = parse_stat_batch(paths, out) if out.strip() else []
    found = {r.path for r in records}
    for path in paths:
        if path not in found:
            issue(str(path), "native stat unavailable")
    if code or err:
        issue(str(paths[0]), "native stat partial: " + err[:200])
    return accessible + records


def walk_privileged(
    root: Path, *, exclusions: list[Path], issue, directory, cancelled
) -> Iterator[WalkEntry]:
    if not root.is_absolute() or ".." in root.parts:
        raise ValueError("Invalid read-only scope")
    command = ["/usr/bin/sudo", "-n", "/usr/bin/find", "-x", str(root)]
    # Avoid traversing our growing journal. Expressions are literal argv, not shell text.
    scoped = [p for p in exclusions if p == root or p.is_relative_to(root)]
    for path in scoped:
        issue(str(path), "scanner-state exclusion")
        command += ["-path", glob.escape(str(path)), "-prune", "-o"]
    command += ["-print0"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None and process.stderr is not None
    buffer = b""
    batch = []
    errors = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "out")
            selector.register(process.stderr, selectors.EVENT_READ, "err")
            while selector.get_map() and not cancelled():
                for key, _ in selector.select(0.1):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if key.data == "err":
                        # Every error line counted, while diagnostics are bounded.
                        errors.extend(chunk)
                        while b"\n" in errors:
                            line, _, rest = errors.partition(b"\n")
                            errors = bytearray(rest)
                            text = line.decode(errors="replace")
                            match = re.match(r"^find: (.*): [^:]+$", text)
                            issue(match[1] if match else str(root), "native find: " + text[:300])
                    else:
                        buffer += chunk
                        while b"\0" in buffer:
                            raw, buffer = buffer.split(b"\0", 1)
                            path = Path(os.fsdecode(raw))
                            if not path.is_relative_to(root):
                                raise ValueError("Native path escaped root")
                            if excluded(path, exclusions):
                                continue
                            batch.append(path)
                            if len(batch) >= 256:
                                for entry in privileged_metadata(batch, issue, cancelled):
                                    if stat.S_ISDIR(entry.metadata.mode) and not directory(entry.metadata):
                                        continue
                                    yield entry
                                batch = []
            if batch and not cancelled():
                for entry in privileged_metadata(batch, issue, cancelled):
                    if stat.S_ISDIR(entry.metadata.mode) and not directory(entry.metadata):
                        continue
                    yield entry
        if errors:
            issue(str(root), "native find: " + errors.decode(errors="replace")[:300])
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=2)
        if process.returncode not in (0, -15) and not cancelled():
            issue(str(root), f"native find exit {process.returncode}")
