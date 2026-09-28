import os
import time

from test_whole_disk_scope import Model

from jev_clean.application.whole_disk import investigate_disk


def test_reused_decisions_do_not_claim_fresh_inference_time(tmp_path):
    root = tmp_path / "Library/Caches/example"
    root.mkdir(parents=True)
    epoch = time.time() - 90 * 86400
    for name in ("a", "b"):
        p = root / name
        p.write_bytes(b"cache")
        os.utime(p, (epoch, epoch))
    report = investigate_disk(
        tmp_path, Model(), "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    reused = [c.decision for c in report.candidates if c.decision.reused]
    assert reused and all(d.elapsed_ms == 0 for d in reused)
