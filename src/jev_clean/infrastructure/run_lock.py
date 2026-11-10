"""One jev-clean run per user owns the local model, the decision cache and the selection."""

from __future__ import annotations

import fcntl
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from jev_clean.infrastructure.trash import directory_fd, secure_dir


@contextmanager
def single_run(home: Path) -> Iterator[None]:
    """Taken before any model load, so a second run never loads a second model copy."""
    state = home / ".local/state/jev-clean"
    secure_dir(state)
    with directory_fd(state) as parent:
        fd = os.open("run.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=parent)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise RuntimeError("Another jev-clean run is active; finish or stop it first") from None
        yield
    finally:
        os.close(fd)
