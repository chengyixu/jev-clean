import os
import time

import pytest

from jev_clean.infrastructure.scanner import scan_candidates


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        ".env.production",
        "settings.yaml",
        "project.toml",
        "private.key",
        "session.token",
        "deploy.sh",
        "source.cpp",
    ],
)
def test_metadata_alone_never_authorizes_configuration_or_source_removal(tmp_path, name):
    path = tmp_path / "Library/Caches/example" / name
    path.parent.mkdir(parents=True)
    path.write_text("unique data")
    old = time.time() - 90 * 86400
    os.utime(path, (old, old))
    item = scan_candidates(tmp_path, open_paths=set()).candidates[0]
    assert not item.selectable and item.decision is None
    assert item.evidence["references"] == "unknown"
