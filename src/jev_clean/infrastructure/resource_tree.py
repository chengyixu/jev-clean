"""Selected-resource metadata sealing and no-overwrite directory restore."""

from __future__ import annotations

import ctypes
import hashlib
import os
import platform
import stat
from pathlib import Path

from jev_clean.infrastructure.paths import directory_fd as directory_fd
from jev_clean.infrastructure.scanner import fingerprint


def tree_manifest(path: Path) -> tuple[str, int, int]:
    """Metadata digest, allocated bytes, descendants; no file contents/symlink targets.

    Run only for selected review and execution. Snapshot ownership and filesystem
    boundaries are execution constraints, never a keep/remove classification.
    """
    digest = hashlib.sha256()
    count = 0
    seen = set()
    with directory_fd(path) as root:
        before = os.fstat(root)
        if before.st_uid != os.getuid():
            raise ValueError("Resource is not current-user owned")
        size = before.st_blocks * 512

        def fail(error):
            raise error

        for current, dirs, files, fd in os.fwalk(".", dir_fd=root, follow_symlinks=False, onerror=fail):
            dirs.sort()
            for name in sorted([*dirs, *files]):
                st = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if st.st_dev != before.st_dev or st.st_uid != os.getuid():
                    raise ValueError("Resource crosses a filesystem/ownership boundary")
                if not (stat.S_ISREG(st.st_mode) or stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode)):
                    raise ValueError("Special entry in selected resource")
                relative = os.path.join(current, name)
                digest.update(os.fsencode(relative) + b"\0")
                digest.update(str((fingerprint(st), st.st_mode, st.st_blocks)).encode() + b"\0")
                if (st.st_dev, st.st_ino) not in seen:
                    size += st.st_blocks * 512
                    seen.add((st.st_dev, st.st_ino))
                count += 1
        if fingerprint(before) != fingerprint(os.fstat(root)):
            raise ValueError("Resource changed during manifest capture")
    return digest.hexdigest(), size, count


def rename_exclusive(name: str, destination: str, source_fd: int, target_fd: int) -> None:
    """Atomic no-replace rename for directories; fail rather than overwrite."""
    libc = ctypes.CDLL(None, use_errno=True)
    symbol, flag = ("renameatx_np", 4) if platform.system() == "Darwin" else ("renameat2", 1)
    function = getattr(libc, symbol, None)
    if function is None:
        raise ValueError("Atomic no-overwrite directory restore unavailable on this platform")
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(source_fd, os.fsencode(name), target_fd, os.fsencode(destination), flag) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
