"""Synthetic post-training cases over the UNCHANGED v8 production observation API.

No actual paths, directory-purpose additions or runtime policy rules. Labels are
training targets only. Cache-owner declarations, activity counterfactuals and
sensitive-format controls must generalize across counts, layouts and suffixes.
"""

from jev_clean.domain.models import Candidate, Fingerprint
from jev_clean.infrastructure.learned_cleanup import observed_state


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
                    item = Candidate(
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
                        evidence={**facts, **changes},
                        unit="directory",
                    )
                    data[split].append(
                        {
                            "family": f"{split}-runtime-{index}-{name}",
                            "label": label,
                            "state": observed_state(item),
                            "scenario": name,
                        }
                    )
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
