"""Observation-shaped authored file-resource corpus, not runtime disposal rules.

Synthetic labels encode the requested review recommendation for documented cache
purpose/idle targets, while ambiguous or mixed resources defer. Namespace placement
is not proof every app obeys its contract. Future independent real-data review is
still needed; no claim this corpus certifies safe deletion.
"""

from jev_clean.domain.models import Candidate, Fingerprint
from jev_clean.infrastructure.evidence import CACHE_NAMESPACE_CONTRACT, LOG_NAMESPACE_CONTRACT
from jev_clean.infrastructure.learned_cleanup import observed_state


def build_file_corpus():
    splits = {"train": [], "dev": [], "final": []}
    formats = {
        "train": [".bin:4", ".json:2, .db:1", "[none]:8", ".log:5", ".gz:2", ".dat:3"],
        "dev": [".cache:4", ".blob:3"],
        "final": [".index:2", ".tmp:4", ".data:6"],
    }
    split_counts = {"train": (2, 8, 32), "dev": (5, 13, 41), "final": (7, 17, 53)}
    for split, extensions in formats.items():
        for index, ext in enumerate(extensions):
            for variant in range(3):
                facts = {
                    "file_extensions": ext,
                    "directory_extensions": "[none]:2" if variant else "unknown",
                    "sampled_entries": str(split_counts[split][variant]),
                    "observation_scope": "partial immediate-entry sample; no subtree purity claim"
                    if variant == 1
                    else "all immediate entries; descendants uninspected",
                }
                scenarios = [
                    ("cache-idle", 0, "macos-cache", False, {}),
                    ("cache-active", 2, "macos-cache", True, {}),
                    ("cache-activity-unknown", 1, "macos-cache", None, {}),
                    ("unverified-idle", 1, "unverified", False, {}),
                    ("unverified-active", 2, "unverified", True, {}),
                    (
                        "cache-media-mixed",
                        1,
                        "macos-cache",
                        False,
                        {"directory_extensions": ".photoslibrary:1", "file_extensions": ".jpg:4"},
                    ),
                    (
                        "cache-source-mixed",
                        1,
                        "macos-cache",
                        False,
                        {"file_extensions": ".py:3, .toml:1, .key:1"},
                    ),
                    (
                        "cache-media-single",
                        1,
                        "macos-cache",
                        False,
                        {"file_extensions": (".heic:3", ".png:2", ".nef:7")[variant]},
                    ),
                    (
                        "cache-credential-single",
                        1,
                        "macos-cache",
                        False,
                        {"file_extensions": (".p12:2", ".wallet:1", ".pem:4")[variant]},
                    ),
                    (
                        "cache-source-single",
                        1,
                        "macos-cache",
                        False,
                        {"file_extensions": (".swift:3", ".rs:2", ".ipynb:6")[variant]},
                    ),
                    (
                        "cache-model-single",
                        1,
                        "macos-cache",
                        False,
                        {"file_extensions": (".gguf:2", ".safetensors:1", ".raw:5")[variant]},
                    ),
                    (
                        "cache-db-ambiguous",
                        1,
                        "macos-cache",
                        False,
                        {"file_extensions": (".sqlite:2", ".wal:1", ".sqlite3:4")[variant]},
                    ),
                    ("logs-idle", 1, "macos-diagnostic-log", False, {}),
                    (
                        "personal-media",
                        1,
                        "unverified",
                        False,
                        {"file_extensions": ".heic:2, .jpg:4", "directory_extensions": ".photoslibrary:1"},
                    ),
                    (
                        "personal-credentials",
                        1,
                        "unverified",
                        False,
                        {"file_extensions": ".pem:2, .p12:1, .kdbx:1"},
                    ),
                ]
                for name, label, role, active, overrides in scenarios:
                    evidence = {
                        **facts,
                        **overrides,
                        "storage_namespace": role,
                        "namespace_contract": CACHE_NAMESPACE_CONTRACT
                        if role == "macos-cache"
                        else LOG_NAMESPACE_CONTRACT
                        if role == "macos-diagnostic-log"
                        else "unknown",
                    }
                    item = Candidate(
                        name,
                        "/synthetic/resource",
                        "file",
                        8_000_000,
                        80 * 86400,
                        Fingerprint(1, 1, 4096, 0, 0, 501, 1),
                        False,
                        False,
                        True,
                        active,
                        evidence=evidence,
                        unit="directory",
                    )
                    splits[split].append(
                        {
                            "family": f"{split}-{index}-{name}",
                            "label": label,
                            "state": observed_state(item),
                            "name": "not in classifier state",
                            "scenario": name,
                        }
                    )
    # Distinct heldout observation counts prevent negative cases being silently
    # lost across splits. Drop repeats WITHIN a split only; cross-split duplicates
    # must fail validate_splits, never be filtered from heldouts.
    for split in splits:
        seen = set()
        filtered = []
        for row in splits[split]:
            if row["state"] in seen:
                continue
            seen.add(row["state"])
            filtered.append(row)
        splits[split] = filtered
    return splits


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = build_file_corpus()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print({k: len(v) for k, v in data.items()})
