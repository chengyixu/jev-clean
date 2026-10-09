"""Bounded LOCAL Laya scorer fine-tune/evaluation, never a production classifier.

Only authored synthetic observations are used. The same pinned Laya encoder and
head produce cached marker features. The existing scorer's weights are learned
with cross-entropy; no path/tag gate enters raw prediction metrics. Outputs remain
private unless explicitly reviewed. Installed application is not changed.
"""

import argparse
import hashlib
import json
import random
import time
from pathlib import Path

QUESTION = {
    "type": "choice",
    "instructions": "What does the observed evidence establish about the data in this resource?",
    "criteria": {
        "A": "The data is disposable and no longer needed.",
        "B": "Whether the data is needed is unknown or uncertain.",
        "C": "The data is needed and must be retained.",
    },
}

# Family split is authored BEFORE running inference. Class ids: A=remove,
# B=review, C=keep. Descriptions are independent labels, not model teacher output.
FAMILIES = {
    "train": [
        (
            "photo-originals",
            2,
            "These photographs are the only originals of family memories. No other copy exists. The owner needs them.",
        ),
        (
            "business-records",
            2,
            "The database holds unique business records required by the user. It is not generated disposable data.",
        ),
        (
            "source-work",
            2,
            "The source files contain unpublished work required by an active project. The work cannot be regenerated.",
        ),
        (
            "secret-recovery",
            2,
            "These secret keys are required to recover encrypted backups. There is no replacement copy.",
        ),
        (
            "required-vm",
            2,
            "The application needs this virtual machine to start. It stores unique local work and is currently stopped.",
        ),
        (
            "support-case",
            2,
            "These logs are evidence needed by the owner for an unresolved support investigation.",
        ),
        (
            "unknown-storage",
            1,
            "Purpose, application references, ownership of data and regenerability have not been established.",
        ),
        (
            "unknown-version",
            1,
            "Two versions of the data are present. Which one is current and whether either is unused are unknown.",
        ),
        (
            "mixed-cache",
            1,
            "This folder contains both generated data and other files. Whether the other files are unique is unknown.",
        ),
        (
            "offline-ambiguity",
            1,
            "No process has this data open. Nothing establishes whether it is needed later or can be reconstructed.",
        ),
        (
            "cache-label",
            1,
            "A directory name suggests cache. No owner declaration or reference check was performed. Its contents are unverified.",
        ),
        (
            "partial-observations",
            1,
            "Only file size and age were measured. The role and future need of the data are unknown.",
        ),
        (
            "unreferenced-packages",
            0,
            "The package manager confirms these cached downloads have no remaining references. They can be downloaded again and hold no unique work.",
        ),
        (
            "test-outputs",
            0,
            "A completed disposable test generated these temporary outputs. All outputs can be regenerated. They have no remaining use.",
        ),
        (
            "render-intermediates",
            0,
            "These redundant render intermediates are no longer needed. The final output is verified elsewhere and the owner wants the intermediates removed.",
        ),
        (
            "obsolete-installer",
            0,
            "Installation finished and the application runs independently. The owner explicitly no longer wants this redundant installer.",
        ),
        (
            "closed-diagnostics",
            0,
            "These completed diagnostic files are unneeded. There is no investigation or retained evidence requirement and no unique user data.",
        ),
        (
            "cache-owner",
            0,
            "The generating application declares this entire tree to be regenerable cached data. The cache is no longer needed and contains no unique work.",
        ),
    ],
    "dev": [
        (
            "music-recording",
            2,
            "The recordings are the only takes from a session the user needs. Deletion would destroy the original work.",
        ),
        (
            "active-compile",
            2,
            "The compiler is using these objects in a build currently running. The current build needs them.",
        ),
        (
            "incomplete-download",
            1,
            "A download is incomplete. Whether the user wishes to resume it and whether the source remains available are unknown.",
        ),
        (
            "unidentified-archive",
            1,
            "The archive is old and large. Its contents and whether another copy exists have not been investigated.",
        ),
        (
            "discarded-analysis",
            0,
            "The owner discarded this completed analysis. Its generated intermediate tables have no remaining use and can be reproduced.",
        ),
        (
            "old-transcode",
            0,
            "The disposable transcode preview is no longer wanted. The original and final export are verified and retained.",
        ),
    ],
    "test": [
        (
            "mail-history",
            2,
            "These messages are the user's unique correspondence. The mail application needs the account history.",
        ),
        (
            "offline-weights",
            2,
            "These model weights are needed for offline work. Their download source no longer exists and no other copy is available.",
        ),
        (
            "signed-agreements",
            2,
            "These signed agreements are irreplaceable legal records required by the owner.",
        ),
        (
            "backup-only",
            2,
            "The project was lost. This backup is the only remaining restorable copy and must be kept.",
        ),
        (
            "misnamed-cache",
            2,
            "Although the folder is called cache, it contains the only ledger of account balances. The ledger is needed.",
        ),
        (
            "owner-unverified",
            1,
            "An app identifier matches the folder. There is no evidence of dependency, obsolescence or whether the data is disposable.",
        ),
        (
            "version-uncertain",
            1,
            "A bundle appears older than another bundle. No runtime reference or current-version evidence is available.",
        ),
        (
            "ambiguous-photos",
            1,
            "Image files are present. Whether they are previews or unique originals has not been established.",
        ),
        (
            "no-information",
            1,
            "No evidence establishes what the data is used for or whether the user needs it.",
        ),
        (
            "build-completed",
            0,
            "A terminated build left regenerable intermediates. The build tool confirms they are unused and no unique project work is present.",
        ),
        (
            "discarded-export",
            0,
            "The owner explicitly requests removal of this redundant generated export. The original and verified backup remain.",
        ),
        (
            "package-unreachable",
            0,
            "The package manager identifies this cache object as unreachable from every installed environment. It is reproducible and unneeded.",
        ),
        (
            "temporary-index",
            0,
            "This obsolete index is generated entirely from retained source data. The owner no longer needs it and can recreate it.",
        ),
        (
            "negative-not-cache",
            2,
            "This resource is NOT a disposable cache. It contains personal photographs with no backup. The user needs them.",
        ),
        (
            "negative-not-unique",
            0,
            "This resource does NOT contain original photographs. It contains only unneeded reproducible thumbnails; originals are retained elsewhere.",
        ),
    ],
}


def corpus():
    rows = {}
    for split, families in FAMILIES.items():
        rows[split] = []
        for family, label, observation in families:
            for version in range(4 if split == "train" else 2):
                # Balanced irrelevant metadata: label is not encoded by size/name/age.
                suffix = [
                    "Measured size is 2 GB. Last change was 80 days ago. No open handle was observed.",
                    "Measured size is 3 MB. Last change was yesterday. Open handles are unknown.",
                    "The resource label is untrusted. Size and last access cannot establish disposability.",
                    "Observation concerns the entire directory. File contents were not uploaded.",
                ][version]
                rows[split].append(
                    {
                        "family": family,
                        "label": label,
                        "state": f"Observed resource evidence: {observation} {suffix}",
                    }
                )
    return rows


def validate_splits(splits):
    families, texts = {}, {}
    for split, rows in splits.items():
        for row in rows:
            if row["family"] in families and families[row["family"]] != split:
                raise ValueError("Semantic family leaked across splits")
            key = hashlib.sha256(row["state"].strip().encode()).hexdigest()
            if key in texts and texts[key] != split:
                raise ValueError("Identical text leaked across splits")
            if row["label"] not in (0, 1, 2):
                raise ValueError("Invalid label")
            families[row["family"]] = split
            texts[key] = split


def metrics(labels, predictions):
    if len(labels) != len(predictions) or not labels:
        raise ValueError("Metric arrays need equal nonempty lengths")
    true_removes = sum(v == 0 for v in labels)
    correctly_removed = sum(y == p == 0 for y, p in zip(labels, predictions, strict=True))
    return {
        "cases": len(labels),
        "correct": sum(y == p for y, p in zip(labels, predictions, strict=True)),
        "false_remove": sum(y != 0 and p == 0 for y, p in zip(labels, predictions, strict=True)),
        "removal_recall": correctly_removed / true_removes if true_removes else None,
        "confusion": [
            [sum(y == i and p == j for y, p in zip(labels, predictions, strict=True)) for j in range(3)]
            for i in range(3)
        ],
    }


def development_candidate(runs):
    """Never choose a seed using final/test performance."""
    if not runs:
        raise ValueError("No candidates")
    return min(runs, key=lambda r: (r["dev"]["false_remove"], -r["dev"]["correct"], r["seed"]))


def deployment_assessment(baseline, candidate):
    """Offline experiment assessment, NOT a per-resource runtime policy.

    Passing only admits further validation; small synthetic holdouts never certify
    real deletion safety. Preserve all raw classifier errors in the measurements.
    """
    eligible = bool(
        candidate["cases"] == baseline["cases"]
        and candidate["false_remove"] == 0
        and candidate["correct"] >= baseline["correct"]
        and candidate["removal_recall"] is not None
        and candidate["removal_recall"] >= baseline["removal_recall"]
    )
    return {
        "eligible_for_further_validation": eligible,
        "reason": "Further real-data validation required; no safety certification"
        if eligible
        else "Raw held-out errors or useful-removal regression; do not deploy",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=160)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    args = parser.parse_args()
    if not 1 <= args.steps <= 400 or not args.seeds or len(args.seeds) > 3:
        parser.error("Bounded experiment requires 1–400 steps and 1–3 seeds")
    # MLX imports are lazy: corpus/metric tests stay portable and hermetic.
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as optim
    import numpy as np
    from laya_mlx.agent import collate_items
    from mlx.utils import tree_flatten, tree_unflatten

    from jev_clean.infrastructure.model import MODEL_ID, MODEL_REVISION, LayaAdvisor

    data = corpus()
    validate_splits(data)
    advisor = LayaAdvisor()
    advisor.load()
    backend = advisor._shared
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    (args.output / "synthetic-corpus.json").write_text(json.dumps(data, indent=2))
    started = time.perf_counter()
    features, gold, base = {}, {}, {}
    for split, rows in data.items():
        vectors, raw, targets = [], [], []
        for row in rows:
            items, _ = backend.prepare(row["state"], {"disposition": QUESTION})
            token_count = len(backend.tok(row["state"], add_special_tokens=False)["input_ids"])
            prefix, _ = backend.prepare("", {"disposition": QUESTION})
            if token_count + len(prefix[0]["ids"]) > backend.cfg["max_len"]:
                raise ValueError("Experiment evidence exceeds context")
            batch = collate_items(items, backend.tok.pad_token_id)
            tensors = {k: mx.array(v) for k, v in batch.items()}
            h = backend.model.encoder(tensors["input_ids"], tensors["attention_mask"])
            h = h + backend.model.type_emb(tensors["qtype"])[:, None, :]
            h = backend.model.head(h, tensors["attention_mask"][:, None, None, :].astype(mx.bool_))
            marker = h[mx.arange(h.shape[0])[:, None], tensors["marker_pos"]]
            # Validate the cached-feature boundary against the real runtime forward.
            cached = backend.model.scorer(marker).squeeze(-1).astype(mx.float32)
            actual, _ = backend.forward(batch)
            mx.eval(marker, cached, actual)
            if not np.allclose(np.asarray(cached), np.asarray(actual), atol=0.005, rtol=0.005):
                raise ValueError("Feature adapter does not match native Laya logits")
            vectors.append(np.asarray(marker[0]).astype(np.float32))
            targets.append(row["label"])
            raw.append(int(np.asarray(actual)[0].argmax()))
        features[split] = mx.array(np.stack(vectors))
        gold[split] = targets
        base[split] = metrics(targets, raw)
        print("baseline", split, json.dumps(base[split]), flush=True)
    # Baseline predictions do not influence labels, heldout cases or optimizer selection.
    original = dict(tree_flatten(backend.model.scorer.parameters()))
    runs = []
    for seed in args.seeds:
        mx.random.seed(seed)
        rng = random.Random(seed)
        scorer = nn.Sequential(
            nn.LayerNorm(backend.encoder_cfg["hidden_size"]),
            nn.Linear(backend.encoder_cfg["hidden_size"], backend.encoder_cfg["hidden_size"]),
            nn.GELU(),
            nn.Linear(backend.encoder_cfg["hidden_size"], 1),
        )
        scorer.update(tree_unflatten({k: v.astype(mx.float32) for k, v in original.items()}.items()))
        optimizer = optim.AdamW(learning_rate=1e-4, weight_decay=0.01)

        def loss_fn(model, x, y):
            logits = model(x).squeeze(-1)
            return nn.losses.cross_entropy(logits, y, reduction="mean")

        gradient = nn.value_and_grad(scorer, loss_fn)
        best = None
        best_weights = None
        best_step = 0
        t = time.perf_counter()
        for step in range(1, args.steps + 1):
            indices = rng.sample(range(len(gold["train"])), min(12, len(gold["train"])))
            ix = mx.array(indices)
            y = mx.array([gold["train"][i] for i in indices])
            loss, grad = gradient(scorer, features["train"][ix], y)
            optimizer.update(scorer, grad)
            mx.eval(scorer.parameters(), optimizer.state, loss)
            if step % 20 == 0 or step == args.steps:
                logits = scorer(features["dev"]).squeeze(-1)
                mx.eval(logits)
                dev = metrics(gold["dev"], np.asarray(logits).argmax(axis=1).tolist())
                rank = (dev["false_remove"], -dev["correct"])
                if best is None or rank < best:
                    best = rank
                    best_step = step
                    best_weights = {k: mx.array(v) for k, v in tree_flatten(scorer.parameters())}
                    mx.eval(best_weights)
                print("train", seed, step, "loss", round(float(loss.item()), 4), "dev", dev, flush=True)
        scorer.update(tree_unflatten(best_weights.items()))
        report = {
            "seed": seed,
            "selected_step": best_step,
            "train_seconds": round(time.perf_counter() - t, 3),
        }
        predictions = {}
        for split in ("train", "dev", "test"):
            logits = scorer(features[split]).squeeze(-1)
            mx.eval(logits)
            pred = np.asarray(logits).argmax(axis=1).tolist()
            report[split] = metrics(gold[split], pred)
            predictions[split] = [
                {"family": r["family"], "expected": r["label"], "predicted": p}
                for r, p in zip(data[split], pred, strict=True)
            ]
        mx.save_safetensors(str(args.output / f"scorer-seed-{seed}.safetensors"), best_weights)
        report["predictions"] = predictions
        runs.append(report)
        print("RESULT", json.dumps({k: v for k, v in report.items() if k != "predictions"}), flush=True)
    selected = development_candidate(runs)
    result = {
        "selected_seed_by_dev": selected["seed"],
        "assessment": deployment_assessment(base["test"], selected["test"]),
        "base_model": MODEL_ID,
        "base_revision": MODEL_REVISION,
        "question": QUESTION,
        "feature_seconds": round(time.perf_counter() - started - sum(r["train_seconds"] for r in runs), 3),
        "baseline": base,
        "runs": runs,
        "limitations": "Small authored English synthetic observations, family-disjoint splits but not an independent real filesystem test. Only existing Laya scorer fine-tuned with frozen encoder/head, not RLCD/full fine-tune. Evidence supplied in synthetic text is richer than production collectors can establish. No permission gates or confidence thresholds in metrics. Checkpoint selected on dev only; final holdout is reporting-only. No installed model, app, provider or personal data changed. No guarantee of safe deletion.",
    }
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    for path in args.output.iterdir():
        if path.is_file():
            path.chmod(0o600)


if __name__ == "__main__":
    main()
