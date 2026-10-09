"""Independently observed disposable-cache declarations; never infer from names.

CACHEDIR.TAG is a cache-owner declaration of regenerable data, not proof of no
regeneration cost or a substitute for model/human review. Read only its specified
43-byte header. Revalidate the declaration itself before any move.
Specification: https://bford.info/cachedir/
"""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

from jev_clean.domain.models import DisposalEvidence
from jev_clean.infrastructure.paths import directory_fd

CACHE_SIGNATURE = b"Signature: 8a477f597d28d172789f06886806bc55"


def observe_disposal(path: Path, home: Path, *, directory: bool) -> DisposalEvidence | None:
    if not path.is_absolute() or not home.is_absolute() or ".." in path.parts:
        return None
    if not path.is_relative_to(home) or path == home:
        return None
    start = path if directory else path.parent
    for parent in (start, *start.parents):
        if parent == home or not parent.is_relative_to(home):
            break
        if path == parent / "CACHEDIR.TAG":
            return None
        try:
            with directory_fd(parent) as fd:
                marker = os.open("CACHEDIR.TAG", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                try:
                    st = os.fstat(marker)
                    if (
                        not stat.S_ISREG(st.st_mode)
                        or st.st_uid != os.getuid()
                        or st.st_nlink != 1
                        or st.st_mode & 0o022
                    ):
                        return None
                    header = os.read(marker, len(CACHE_SIGNATURE))
                    after = os.fstat(marker)
                    identity = (
                        st.st_dev,
                        st.st_ino,
                        st.st_size,
                        st.st_mtime_ns,
                        st.st_ctime_ns,
                        st.st_uid,
                        st.st_nlink,
                    )
                    current = (
                        after.st_dev,
                        after.st_ino,
                        after.st_size,
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                        after.st_uid,
                        after.st_nlink,
                    )
                    if header != CACHE_SIGNATURE or identity != current:
                        return None
                    token = hashlib.sha256(header + repr(identity).encode()).hexdigest()
                    return DisposalEvidence("cachedir-tag-v1", str(parent), token)
                finally:
                    os.close(marker)
        except FileNotFoundError:
            continue
        except OSError:
            return None
    return None


def require_current_disposal(
    path: Path, home: Path, expected: DisposalEvidence | None, *, directory: bool
) -> None:
    current = observe_disposal(path, home, directory=directory)
    if expected is None or current is None or not expected.covers(str(path)) or current != expected:
        raise ValueError("Disposal evidence missing or changed; this target is not authorized for cleanup")
