"""User-only, file-level, journaled Trash moves. No recursive deletes, no root."""

from __future__ import annotations

import fcntl
import json
import os
import re
import stat
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from jev_clean.domain.models import Candidate, Fingerprint, MoveResult
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.scanner import fingerprint, no_symlink_ancestors


@contextmanager
def directory_fd(path: Path):
    """Open every component without following symlinks, not just the final one."""
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Expected canonical absolute path")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        yield fd
    finally:
        os.close(fd)


def secure_dir(path: Path) -> None:
    if not no_symlink_ancestors(path):
        raise ValueError("Symlink in private state/Trash path")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    st = path.stat()
    if st.st_uid != os.getuid() or st.st_mode & 0o022:
        raise ValueError("Private directory must be owned and not writable by other users")


def save_private(path: Path, data: dict) -> None:
    secure_dir(path.parent)
    with directory_fd(path.parent) as parent:
        temporary = f".write-{uuid.uuid4().hex}"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "w") as output:
                json.dump(data, output, indent=2)
                output.flush()
                os.fsync(output.fileno())
            os.rename(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass


def read_private(path: Path) -> dict:
    with directory_fd(path.parent) as parent:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        with os.fdopen(fd) as source:
            st = os.fstat(source.fileno())
            if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_size > 16 * 1024 * 1024:
                raise ValueError("Invalid report/journal file")
            return json.load(source)


class TrashStore:
    def __init__(self, home: Path):
        self.home = Path(os.path.abspath(home))
        self.state = self.home / ".local/state/jev-clean"

    @contextmanager
    def locked(self):
        if os.geteuid() == 0:
            raise ValueError("Never run cleanup as root")
        secure_dir(self.state)
        with directory_fd(self.state) as parent:
            fd = os.open(".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                yield
            finally:
                os.close(fd)

    def move(self, selected: list[Candidate], *, open_paths: set[str] | None) -> MoveResult:
        result = MoveResult(uuid.uuid4().hex)
        with self.locked():
            batch = self.home / ".Trash" / f"jev-clean-{result.batch_id}"
            secure_dir(batch)
            journal_path = self.state / f"{result.batch_id}.json"
            journal: dict = {"schema_version": 1, "id": result.batch_id, "entries": []}
            save_private(journal_path, journal)
            seen: set[str] = set()
            with directory_fd(batch) as target:
                for item in selected:
                    try:
                        source = Path(item.path)
                        if not apply_policy(item, item.decision).selectable:
                            raise ValueError("Mandatory model approval or execution readiness absent")
                        if item.path in seen:
                            raise ValueError("Duplicate selection")
                        seen.add(item.path)
                        self.validate_source(source)
                        if not item.scan_complete:
                            raise ValueError("Original scan incomplete")
                        with directory_fd(source.parent) as parent:
                            current = os.stat(source.name, dir_fd=parent, follow_symlinks=False)
                            if fingerprint(current) != item.fingerprint:
                                raise ValueError("File identity changed since review")
                            if not stat.S_ISREG(current.st_mode) or current.st_uid != os.getuid():
                                raise ValueError("Executor requires a current-user regular file")
                            active = None if open_paths is None else str(source) in open_paths
                            if active != item.open_file:
                                raise ValueError("Activity evidence changed since model review; reassess")
                            token = uuid.uuid4().hex
                            entry = {
                                "source": str(source),
                                "file": token,
                                "state": "pending",
                                "fingerprint": asdict(item.fingerprint),
                                "bytes": item.allocated_bytes,
                            }
                            journal["entries"].append(entry)
                            save_private(journal_path, journal)
                            # Verify again at the syscall boundary; parent directory held open.
                            if (
                                fingerprint(os.stat(source.name, dir_fd=parent, follow_symlinks=False))
                                != item.fingerprint
                            ):
                                raise ValueError("File changed at execution")
                            os.rename(source.name, token, src_dir_fd=parent, dst_dir_fd=target)
                            after = os.stat(token, dir_fd=target, follow_symlinks=False)
                            entry["fingerprint"] = asdict(fingerprint(after))
                            entry["state"] = "staged"
                            save_private(journal_path, journal)
                            result.moved += 1
                            result.staged_bytes += item.allocated_bytes
                    except (OSError, ValueError) as error:
                        result.failed.append(f"{item.path}: {error}")
            return result

    def validate_source(self, source: Path) -> None:
        if not source.is_absolute() or ".." in source.parts:
            raise ValueError("Expected canonical absolute target")
        # The mover cannot relocate its own transaction state or a staged item.
        if source.is_relative_to(self.state) or source.is_relative_to(self.home / ".Trash"):
            raise ValueError("Target conflicts with the executor's journal/Trash")

    def history(self) -> list[dict]:
        if not self.state.exists():
            return []
        return [
            read_private(p)
            for p in sorted(self.state.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            if re.fullmatch("[a-f0-9]{32}.json", p.name)
        ]

    def restore(self, batch_id: str) -> MoveResult:
        if not re.fullmatch("[a-f0-9]{32}", batch_id):
            raise ValueError("Invalid batch ID")
        result = MoveResult(batch_id)
        with self.locked():
            journal_path = self.state / f"{batch_id}.json"
            journal = read_private(journal_path)
            batch = self.home / ".Trash" / f"jev-clean-{batch_id}"
            with directory_fd(batch) as trash:
                for entry in journal["entries"]:
                    if entry["state"] not in ("pending", "staged"):
                        continue
                    try:
                        path = Path(entry["source"])
                        self.validate_source(path)
                        if not re.fullmatch("[a-f0-9]{32}", entry["file"]):
                            raise ValueError("Invalid journal entry")
                        with directory_fd(path.parent) as parent:
                            try:
                                os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                            except FileNotFoundError:
                                pass
                            else:
                                raise ValueError("Source exists; never overwrite")
                            st = os.stat(entry["file"], dir_fd=trash, follow_symlinks=False)
                            old = Fingerprint(**entry["fingerprint"])
                            now = fingerprint(st)
                            # Rename changes ctime. A crash after rename leaves a pending journal.
                            if (now.device, now.inode, now.size, now.mtime_ns, now.uid, now.nlink) != (
                                old.device,
                                old.inode,
                                old.size,
                                old.mtime_ns,
                                old.uid,
                                old.nlink,
                            ):
                                raise ValueError("Staged file changed")
                            if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid():
                                raise ValueError("Unsafe staged file")
                            # Link is atomic and refuses an existing destination; unlike rename it cannot overwrite.
                            os.link(
                                entry["file"],
                                path.name,
                                src_dir_fd=trash,
                                dst_dir_fd=parent,
                                follow_symlinks=False,
                            )
                            os.unlink(entry["file"], dir_fd=trash)
                            entry["state"] = "restored"
                            save_private(journal_path, journal)
                            result.moved += 1
                    except (OSError, ValueError) as error:
                        result.failed.append(f"{entry['source']}: {error}")
        return result
