"""One Apple firmlink mapping for inventory, open-handle checks and cleanup paths."""

from pathlib import Path


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
