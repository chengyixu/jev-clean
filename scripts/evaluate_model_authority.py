"""Read-only real-inference diagnostic. All scenarios are synthetic, not user files.

The first 12 scenarios informed neutral-label prompt selection. The additional
12 were written afterward and frozen before their first inference. Neither set
is a representative or statistically sufficient macOS cleanup benchmark.
"""

import argparse
import json
import platform
from dataclasses import asdict
from pathlib import Path

from jev_clean.domain.models import Candidate, Fingerprint
from jev_clean.infrastructure.model import (
    DISPOSITION_LABELS,
    MODEL_ID,
    MODEL_REVISION,
    QUESTIONS,
    LayaAdvisor,
)

DEVELOPMENT = [
    (
        "unique_database",
        "keep",
        "This SQLite database is the only copy of the user's business records. The application needs it. It has not been modified for 80 days. No process currently has it open.",
    ),
    (
        "required_vm",
        "keep",
        "This disk image is the installed application's current virtual machine. The application needs it to start. The VM is stopped now. It contains unique local work.",
    ),
    (
        "unknown_vm",
        "review",
        "There is an old 10 GB disk image in an application support folder. Its owner, references, contents, and regenerability are unknown. No open handle was observed.",
    ),
    (
        "disposable_cache",
        "remove",
        "The package manager identifies this object as an unreferenced, reproducible download cache. No environment uses it. It can be fetched again. It contains no user work.",
    ),
    (
        "unique_key",
        "keep",
        "This is the only private key for the user's encrypted backups. It is required to recover the backups. It is 900 days old and not open.",
    ),
    (
        "closed_logs",
        "remove",
        "These are completed diagnostic logs. The user does not need them for any investigation. The application has rotated to a different current log. Removing these old logs does not affect the application.",
    ),
    (
        "unknown_log",
        "review",
        "This .xlog file occupies 5 GB. It was modified yesterday. Its format, writer, references, retention needs and contents are unknown.",
    ),
    (
        "active_logs",
        "keep",
        "This file is the active log for an incident currently being investigated. A process is writing to it. The user needs this evidence.",
    ),
    (
        "source",
        "keep",
        "This Python source file contains the user's unpublished project work. It is the only copy. It is needed for an active project, although it was modified 60 days ago.",
    ),
    (
        "new_generated_db",
        "remove",
        "This SQLite file was created today by a completed disposable test run. The test framework identifies it as throwaway generated data. There is no unique work, no active reference and the test can regenerate it.",
    ),
    (
        "old_installer_unknown",
        "review",
        "An old installer archive was found. It is not known whether it is the only copy or whether the user needs it. No application ownership is established.",
    ),
    (
        "old_file_unknown",
        "review",
        "An old, unopened regular file occupies 2 GB. Its purpose, references and unique content are unknown.",
    ),
]
POST_SELECTION = [
    (
        "offline_model",
        "keep",
        "The user depends on these model weights for offline work. The download source no longer exists. The weights are not currently loaded into a process.",
    ),
    (
        "backup_required",
        "keep",
        "This is the last restorable backup of a lost project. The original project was deleted accidentally. Recovery depends on this backup.",
    ),
    (
        "unused_installer",
        "remove",
        "The user explicitly confirms this installer is no longer wanted. Installation completed, the installed app runs independently, and the user has no need for the installer.",
    ),
    (
        "unidentified_archive",
        "review",
        "A large .zip file is in a folder named cache. Its contents, purpose and owner needs have not been checked.",
    ),
    (
        "active_build",
        "keep",
        "The compiler is currently using this generated object file for an ongoing build. Removing it would interrupt the current build.",
    ),
    (
        "completed_render",
        "remove",
        "A completed rendering job left this temporary intermediate. The final output has been verified and saved elsewhere. The intermediate has no remaining use and the owner does not want it.",
    ),
    (
        "version_not_proven_old",
        "review",
        "Two application bundles have different directory names. Their installed versions and runtime references have not been measured. It is not known which is current.",
    ),
    (
        "database_named_cache",
        "keep",
        "The directory is named cache, but the application's documented behavior stores the user's only account ledger here. The ledger must be retained.",
    ),
    (
        "unknown_hardlink",
        "review",
        "This file has two hard links. Nothing is known about the other link, ownership of the data, references or the user's need for this path.",
    ),
    (
        "obsolete_export",
        "remove",
        "This export is a redundant generated copy. The owner explicitly requests its removal and the original plus verified backup are retained. No process references the export.",
    ),
    (
        "retained_incident_log",
        "keep",
        "This old diagnostic log is evidence needed for an unresolved support case. The user must keep it despite its age and size.",
    ),
    (
        "unknown_owner",
        "review",
        "The application identifier matches a directory name. This does not establish that its files are unused. The current application references and regenerability are unknown.",
    ),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    advisor = LayaAdvisor()
    advisor.load()
    question = QUESTIONS["disposition"]
    rows = []
    for split, cases in (("development", DEVELOPMENT), ("post_selection", POST_SELECTION)):
        for name, expected, state in cases:
            raw = advisor.decide(state, "disposition", question["instructions"], question["criteria"])
            item = Candidate(
                name,
                "/synthetic/resource",
                "file",
                4096,
                0,
                Fingerprint(1, 1, 4096, 0, 0, 501, 1),
                True,
                False,
                True,
                evidence={"observations": state},
            )
            structured = advisor.predict(item)
            rows.append(
                {
                    "split": split,
                    "name": name,
                    "expected": expected,
                    "synthetic_evidence": state,
                    "plain_choice": DISPOSITION_LABELS[raw.choice],
                    "raw": asdict(raw),
                    "structured": asdict(structured),
                }
            )
    summary = {}
    for split in ("development", "post_selection"):
        subset = [r for r in rows if r["split"] == split]
        summary[split] = {}
        for representation in ("plain", "structured"):
            choices = [
                r["plain_choice"] if representation == "plain" else r["structured"]["choice"] for r in subset
            ]
            summary[split][representation] = {
                "correct": sum(c == r["expected"] for c, r in zip(choices, subset, strict=True)),
                "total": len(subset),
                "false_remove": sum(
                    c == "remove" and r["expected"] != "remove" for c, r in zip(choices, subset, strict=True)
                ),
                "missed_remove": sum(
                    c != "remove" and r["expected"] == "remove" for c, r in zip(choices, subset, strict=True)
                ),
            }
    result = {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "platform": platform.platform(),
        "load_ms": advisor.load_ms,
        "questions": QUESTIONS,
        "label_mapping": DISPOSITION_LABELS,
        "summary": summary,
        "rows": rows,
        "limitations": "24 synthetic scenarios; not real filesystem ground truth or deletion-safety calibration. Development cases influenced prompt selection. Production evidence collection cannot yet establish all these facts. Model errors are not hidden by a policy veto.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
