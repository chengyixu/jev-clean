import os
import time

from cache_fixtures import declare_cache

from jev_clean.infrastructure.scanner import scan_candidates
from jev_clean.infrastructure.trash import TrashStore


def test_executor_refuses_unassessed_even_if_policy_eligible(tmp_path):
    p = tmp_path / "Library/Caches/test/item"
    declare_cache(p.parent)
    p.write_text("old cache")
    old = time.time() - 90 * 86400
    os.utime(p, (old, old))
    item = next(c for c in scan_candidates(tmp_path, open_paths=set()).candidates if c.path == str(p))
    assert item.eligible
    result = TrashStore(tmp_path).move([item], open_paths=set())
    assert result.moved == 0 and p.exists() and result.failed
