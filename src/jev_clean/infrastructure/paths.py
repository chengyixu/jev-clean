"""One Apple firmlink mapping for inventory, open-handle checks and cleanup paths."""

import os
from contextlib import contextmanager
from pathlib import Path


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


def firmlinks() -> list[tuple[Path, Path]]:
    try:
        lines = Path("/usr/share/firmlinks").read_text().splitlines()
    except OSError:
        return []
    pairs = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) == 2 and parts[0].startswith("/") and ".." not in Path(parts[1]).parts:
            pairs.append((Path("/System/Volumes/Data") / parts[1], Path(parts[0])))
    return sorted(pairs, key=lambda p: len(p[0].parts), reverse=True)


def aliases_covered_elsewhere(root: Path, roots: list[Path], mappings: list[tuple[Path, Path]]) -> list[Path]:
    data = Path("/System/Volumes/Data")
    if root == Path("/") and data in roots and mappings:
        return [data, *[logical for _, logical in mappings]]
    return []


def logical_path(path: Path, mappings: list[tuple[Path, Path]]) -> Path:
    for physical, logical in mappings:
        if path.is_relative_to(physical):
            return logical / path.relative_to(physical)
    return path
