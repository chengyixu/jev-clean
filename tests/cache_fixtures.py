"""Owner-declared synthetic cache metadata, only for temporary test directories."""

from pathlib import Path


def declare_cache(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "CACHEDIR.TAG").write_bytes(b"Signature: 8a477f597d28d172789f06886806bc55\n# synthetic cache\n")
