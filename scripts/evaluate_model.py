"""Real pinned-checkpoint diagnostic evaluation; synthetic metadata, no disk scan or cleanup."""

import argparse
import json
import platform
import statistics
from dataclasses import asdict
from pathlib import Path

from jev_clean.domain.models import Candidate, DiskNode, Fingerprint
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.model import MODEL_ID, MODEL_REVISION, LayaAdvisor


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    advisor = LayaAdvisor()
    advisor.load()
    cases = [
        ("stale-cache", "user-cache", 80, False, True, False, 1, "remove"),
        ("stale-package-cache", "package-cache", 60, False, True, False, 1, "remove"),
        ("rotated-log", "rotated-log", 40, False, True, False, 1, "remove"),
        ("recent-cache", "user-cache", 1, False, True, False, 1, "keep"),
        ("active-cache", "user-cache", 80, True, True, False, 1, "keep"),
        ("unknown-open", "user-cache", 80, None, True, False, 1, "review"),
        ("database", "database", 100, False, True, False, 1, "keep"),
        ("backup", "backup", 100, False, True, False, 1, "keep"),
        ("unknown", "unknown", 100, False, True, False, 1, "review"),
        ("symlink", "user-cache", 100, False, False, True, 1, "keep"),
        ("hardlink", "user-cache", 100, False, True, False, 2, "keep"),
        ("recent-log", "rotated-log", 1, False, True, False, 1, "keep"),
    ]
    rows = []
    for i, (name, kind, days, active, regular, symlink, links, expected) in enumerate(cases):
        item = Candidate(
            name,
            "/Users/demo/Library/Caches/test/item",
            kind,
            840_000_000,
            days * 86400,
            Fingerprint(1, i, 840_000_000, 0, 0, 501, links),
            regular,
            symlink,
            True,
            active,
        )
        decisions = [advisor.predict(item) for _ in range(3)]
        decision = decisions[-1]
        checked = apply_policy(item, decision)
        rows.append(
            {
                "case": name,
                "expected": expected,
                "decision": asdict(decision),
                "samples_ms": [d.elapsed_ms for d in decisions],
                "policy_pass": checked.eligible,
                "selectable": checked.selectable,
            }
        )
    exploration = []
    for hint, size in [
        ("Library/Caches/build-tool", 840_000_000),
        ("Library/Logs/editor", 125_000_000),
        ("Library/Application Support", 20_000_000_000),
        ("opt/homebrew/var/postgresql", 60_000_000_000),
    ]:
        node = DiskNode("/" + hint, size, True, 0)
        exploration.append(
            {
                "hint": hint,
                "decision": asdict(advisor.inspect(node, "status")),
                "purpose": asdict(advisor.classify(node)),
            }
        )
    timings = [v for r in rows for v in r["samples_ms"]]
    accuracy = sum(r["expected"] == r["decision"]["choice"] for r in rows) / len(rows)
    result = {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "load_ms": advisor.load_ms,
        "fixture_count": len(rows),
        "fixture_accuracy": accuracy,
        "dangerous_fixture_selectable_count": sum(r["selectable"] for r in rows if r["expected"] != "remove"),
        "median_inference_ms": statistics.median(timings),
        "samples": rows,
        "exploration": exploration,
        "limitations": "Tiny hand-authored engineering fixtures, not a representative cleanup benchmark. Prompt iteration used similar examples. Scores are not deletion-safety calibration. Guard vetoes are NOT model accuracy.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("samples", "exploration")}, indent=2))


if __name__ == "__main__":
    main()
