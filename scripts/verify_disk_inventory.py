"""Developer-only read-only traversal verification. NOT a model assessment or app mode.

Outputs aggregate coverage only. Uses the same startup-scope resolver and no-follow walker.
"""

import argparse
import json
import sqlite3
import stat
import time
from pathlib import Path

from jev_clean.infrastructure.disk_walk import walk_user
from jev_clean.infrastructure.paths import aliases_covered_elsewhere, firmlinks
from jev_clean.infrastructure.volumes import startup_scope


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output = args.output.absolute()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(args.output.parent / "inventory-seen.sqlite3")
    db.execute("CREATE TABLE IF NOT EXISTS dirs (dev INTEGER,ino INTEGER,PRIMARY KEY(dev,ino)) WITHOUT ROWID")
    db.execute("DELETE FROM dirs")
    s = startup_scope()
    started = time.monotonic()
    counts = {"regular_files": 0, "directories": 0, "symlinks": 0, "other": 0, "issues": 0, "boundaries": 0}

    def directory(meta):
        return db.execute("INSERT OR IGNORE INTO dirs VALUES (?,?)", (meta.device, meta.inode)).rowcount == 1

    def issue(path, reason):
        if reason == "filesystem boundary":
            counts["boundaries"] += 1
        else:
            counts["issues"] += 1

    root_reports = []
    excluded = [args.output.parent, Path("/System/Volumes/Data") / args.output.parent.relative_to("/")]
    for root in s.roots:
        before = counts["regular_files"]
        for entry in walk_user(
            root,
            exclusions=excluded + aliases_covered_elsewhere(root, s.roots, firmlinks()),
            issue=issue,
            directory=directory,
            cancelled=lambda: False,
        ):
            mode = entry.metadata.mode
            if stat.S_ISDIR(mode):
                counts["directories"] += 1
            elif stat.S_ISREG(mode):
                counts["regular_files"] += 1
                if counts["regular_files"] % 100000 == 0:
                    db.commit()
                    print(
                        {
                            "regular_files": counts["regular_files"],
                            "elapsed": round(time.monotonic() - started),
                        },
                        flush=True,
                    )
            elif stat.S_ISLNK(mode):
                counts["symlinks"] += 1
            else:
                counts["other"] += 1
        db.commit()
        root_reports.append({"root": str(root), "regular_files": counts["regular_files"] - before})
        print(root_reports[-1], flush=True)
    db.close()
    result = {
        **counts,
        "roots": root_reports,
        "declared_exclusions": s.exclusions,
        "elapsed_seconds": time.monotonic() - started,
        "model_assessment": False,
        "purpose": "development traversal coverage check only",
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
