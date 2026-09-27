"""Bounded, no-follow, file-level inventory. Never opens file contents."""

from __future__ import annotations

import hashlib
import os
import stat
import time
from dataclasses import replace
from pathlib import Path
from typing import Callable

from jev_clean.domain.models import Candidate, Fingerprint, ScanReport
from jev_clean.domain.policy import ROOTS, apply_policy, kind_for_path


def fingerprint(st: os.stat_result) -> Fingerprint:
    return Fingerprint(
        st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_uid, st.st_nlink
    )


def no_symlink_ancestors(path: Path) -> bool:
    return not any(p.is_symlink() for p in (path, *path.parents))


def candidate_from_stat(path: Path, st: os.stat_result, home: Path, open_paths: set[str] | None) -> Candidate:
    stamp = fingerprint(st)
    identity = hashlib.sha256(f"{path}:{stamp}".encode()).hexdigest()[:20]
    kind = kind_for_path(path, home) or "protected"
    item = Candidate(
        identity,
        str(path),
        kind,
        st.st_blocks * 512,
        max(0, time.time() - st.st_mtime),
        stamp,
        stat.S_ISREG(st.st_mode),
        stat.S_ISLNK(st.st_mode),
        True,
        None if open_paths is None else str(path) in open_paths,
    )
    if st.st_uid != os.getuid():
        item = replace(item, kind="protected")
    return apply_policy(item)


def scan_candidates(
    home: Path,
    *,
    open_paths: set[str] | None,
    max_files: int = 50000,
    seconds: float = 30,
    progress: Callable[[str], None] = lambda _: None,
    cancelled: Callable[[], bool] = lambda: False,
) -> ScanReport:
    start = time.monotonic()
    report = ScanReport()
    home = Path(os.path.abspath(home))
    if not no_symlink_ancestors(home):
        raise ValueError("HOME must not contain symlink ancestors")
    device = home.stat().st_dev
    seen: set[Path] = set()
    for relative, _, _ in ROOTS:
        root = home / relative
        if not root.exists():
            continue
        if not no_symlink_ancestors(root):
            report.warnings.append(f"Skipped symlink root: {root}")
            continue
        progress(f"Inspecting {relative}")

        # fwalk opens each directory; follow_symlinks=False avoids recursive aliasing.
        def walk_error(error: OSError) -> None:
            report.complete = False
            report.warnings.append(f"Permission/IO gap: {error.filename}")

        for current, dirs, files, fd in os.fwalk(root, follow_symlinks=False, onerror=walk_error):
            for directory in list(dirs):
                try:
                    st = os.stat(directory, dir_fd=fd, follow_symlinks=False)
                    if st.st_dev != device or stat.S_ISLNK(st.st_mode):
                        dirs.remove(directory)
                except OSError:
                    dirs.remove(directory)
                    report.complete = False
            for name in files:
                if cancelled() or report.files_seen >= max_files or time.monotonic() - start > seconds:
                    report.complete = False
                    report.warnings.append("Scan interrupted or budget reached; no candidates authorized")
                    break
                path = Path(current) / name
                if path in seen:
                    continue
                seen.add(path)
                report.files_seen += 1
                try:
                    st = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    if st.st_dev != device:
                        continue
                    item = candidate_from_stat(path, st, home, open_paths)
                    if item.allocated_bytes > 0:
                        report.candidates.append(item)
                except OSError as error:
                    report.complete = False
                    report.warnings.append(f"Unreadable metadata: {path}: {error.strerror}")
            if report.warnings and report.warnings[-1].startswith("Scan interrupted"):
                break
        if report.warnings and report.warnings[-1].startswith("Scan interrupted"):
            break
    if not report.complete:
        report.candidates = [apply_policy(replace(c, scan_complete=False)) for c in report.candidates]
    report.candidates.sort(key=lambda c: c.allocated_bytes, reverse=True)
    report.elapsed_ms = (time.monotonic() - start) * 1000
    return report
