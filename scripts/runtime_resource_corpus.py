"""Synthetic post-training cases rendered by the production v9 observation API.

No actual paths or runtime policy rules. Labels are training targets only. Cache-owner
declarations, verified storage roles, activity counterfactuals and sensitive-format
controls must generalize across counts, layouts and suffixes. Every role appears with
matched idle/active/unknown cases so the label follows the documented purpose, not a layout.
"""

from jev_clean.domain.models import Candidate, Fingerprint
from jev_clean.infrastructure.evidence import STORAGE_ROLES
from jev_clean.infrastructure.learned_cleanup import observed_state

# Idle label per verified role: 0 remove, 1 review, 2 keep. Rebuildable build products and
# symbol copies can be proposed when idle; records that cannot be re-created never are.
ROLE_IDLE_LABEL = {
    "xcode-derived-data": 0,
    "xcode-device-support": 0,
    "xcode-archives": 1,
    "simulator-devices": 1,
    "ios-device-backup": 1,
    "user-downloads": 1,
    "mail-store": 2,
    "messages-store": 2,
    "icloud-drive": 2,
    "credential-store": 2,
}
ROLE_LAYOUTS = {
    "train": [(".plist:1", "[none]:3"), (".bin:4", ".noindex:1, [none]:2")],
    "dev": [(".plist:2", "[none]:5"), (".dat:3", "[none]:1")],
    "final": [(".info:1", "[none]:7"), (".idx:2", ".noindex:2")],
}
ROLE_COUNTS = {"train": (5, 23), "dev": (9, 37), "final": (15, 61)}
# Personal formats that turn an otherwise rebuildable resource into a review case.
PERSONAL_FORMATS = {
    "train": {
        "repository": ("", ".git:1, [none]:2"),
        "documents": (".pdf:3", "[none]:1"),
        "archives": (".zip:2", "[none]:1"),
        "mail": (".emlx:6", "[none]:1"),
        "credentials": (".gpg:1", "[none]:2"),
    },
    "dev": {
        "repository": (".swift:2", ".git:1"),
        "documents": (".docx:1", "[none]:3"),
        "archives": (".7z:1", "[none]:2"),
        "mail": (".mbox:2", "[none]:2"),
        "credentials": (".keychain-db:1", "[none]:1"),
    },
    "final": {
        "repository": (".rs:4", ".git:1, [none]:1"),
        "documents": (".pages:2", "[none]:2"),
        "archives": (".tar:1", "[none]:3"),
        "mail": (".eml:9", "[none]:1"),
        "credentials": (".p8:1", "[none]:3"),
    },
}


def synthetic_resource(evidence, active):
    return Candidate(
        "synthetic",
        "/synthetic/resource",
        "unknown",
        1_000_000,
        86400,
        Fingerprint(1, 1, 4096, 0, 0, 501, 1),
        False,
        False,
        True,
        active,
        evidence=evidence,
        unit="directory",
    )


def role_cases(split):
    """Matched role counterfactuals: same layout, only the role, activity or formats change."""
    rows = []
    for role, idle in ROLE_IDLE_LABEL.items():
        for layout, (files, directories) in enumerate(ROLE_LAYOUTS[split]):
            count = ROLE_COUNTS[split][layout]
            facts = {
                "storage_namespace": role,
                "namespace_contract": STORAGE_ROLES[role][1],
                "sampled_entries": str(count),
                "file_extensions": files,
                "directory_extensions": directories,
                "observation_scope": "all immediate entries; descendants uninspected",
            }
            scenarios = [
                ("idle", idle, False, {}),
                ("active", 2, True, {}),
                ("unknown-activity", 1 if idle == 0 else idle, None, {}),
            ]
            if idle == 0:
                for name, (personal_files, personal_dirs) in PERSONAL_FORMATS[split].items():
                    changes = {"directory_extensions": personal_dirs}
                    if personal_files:
                        changes["file_extensions"] = personal_files
                    scenarios.append((f"personal-{name}", 1, False, changes))
            for name, label, active, changes in scenarios:
                rows.append(
                    {
                        "family": f"{split}-role-{role}-{layout}-{name}",
                        "label": label,
                        "state": observed_state(synthetic_resource({**facts, **changes}, active)),
                        "scenario": f"role-{name}",
                    }
                )
    # Rebuildable cache namespace and owner declaration with the same personal formats.
    for name, (personal_files, personal_dirs) in PERSONAL_FORMATS[split].items():
        for basis, extra in (
            ("cache", {"storage_namespace": "macos-cache"}),
            ("declared", {"disposal_basis": "observed valid CACHEDIR.TAG cache declaration"}),
        ):
            facts = {
                "storage_namespace": "unverified",
                "sampled_entries": str(ROLE_COUNTS[split][0] + 2),
                "file_extensions": personal_files or ".bin:2",
                "directory_extensions": personal_dirs,
                "observation_scope": "all immediate entries; descendants uninspected",
                **extra,
            }
            rows.append(
                {
                    "family": f"{split}-{basis}-personal-{name}",
                    "label": 1,
                    "state": observed_state(synthetic_resource(facts, False)),
                    "scenario": f"{basis}-personal-{name}",
                }
            )
    return rows


def build_runtime_corpus():
    from file_resource_corpus import build_file_corpus

    data = build_file_corpus()
    formats = {
        "train": [(".tag", ".json"), (".o", ".d"), (".cache", ".blob")],
        "dev": [(".rmeta", ".rlib"), (".tag", ".data")],
        "final": [(".obj", ".dep"), (".tag", ".index")],
    }
    counts = {"train": (3, 11, 29), "dev": (7, 19, 43), "final": (13, 31, 67)}
    sensitive = {
        "source": (".swift", ".rs", ".ipynb"),
        "media": (".heic", ".nef", ".mov"),
        "credentials": (".pem", ".p12", ".wallet"),
        "model": (".safetensors", ".gguf", ".raw"),
        "database": (".sqlite", ".sqlite3", ".wal"),
    }
    for split, suffixes in formats.items():
        for index, pair in enumerate(suffixes):
            for variant, count in enumerate(counts[split]):
                facts = {
                    "storage_namespace": "unverified",
                    "sampled_entries": str(count + 4),
                    "file_extensions": f"{pair[0]}:1, {pair[1]}:2",
                    "directory_extensions": f"[none]:{count + 1}",
                    "observation_scope": "all immediate entries; descendants uninspected",
                    "disposal_basis": "observed valid CACHEDIR.TAG cache declaration",
                }
                scenarios = [
                    ("declared-idle", 0, False, {}),
                    ("declared-active", 2, True, {}),
                    ("declared-unknown-activity", 1, None, {}),
                    (
                        "undeclared-idle",
                        1,
                        False,
                        {"disposal_basis": "none observed; disposability unverified"},
                    ),
                ]
                for name, options in sensitive.items():
                    scenarios.append(
                        (f"declared-{name}", 1, False, {"file_extensions": f"{options[variant]}:3"})
                    )
                for name, label, active, changes in scenarios:
                    item = synthetic_resource({**facts, **changes}, active)
                    data[split].append(
                        {
                            "family": f"{split}-runtime-{index}-{name}",
                            "label": label,
                            "state": observed_state(item),
                            "scenario": name,
                        }
                    )
    for split in data:
        data[split].extend(role_cases(split))
    # Preserve all semantic controls. Only exact same-label repeats within one
    # split may collapse; contradictory targets or cross-split leakage fail.
    for split, rows in data.items():
        unique = {}
        for row in rows:
            prior = unique.get(row["state"])
            if prior is not None and prior["label"] != row["label"]:
                raise ValueError("Identical observations have contradictory labels")
            unique.setdefault(row["state"], row)
        data[split] = list(unique.values())
    return data


if __name__ == "__main__":
    import argparse
    import json

    from laya_cleanup_experiment import validate_splits

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    corpus = build_runtime_corpus()
    validate_splits(corpus)
    with open(args.output, "w") as stream:
        json.dump(corpus, stream, indent=2)
    print({key: len(value) for key, value in corpus.items()})
