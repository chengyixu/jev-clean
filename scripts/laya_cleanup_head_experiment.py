"""Bounded native MLX Laya head training; synthetic research, never runtime policy.

Frozen encoder/type embeddings; train the ORIGINAL Laya decision head and scorer.
The final family holdout was authored after the earlier scorer run and frozen
before the head run. It is now exposed; future tuning needs a new final holdout.
No application installation, full-checkpoint replacement or user files are touched.
"""

import argparse
import json
import random
import time
from pathlib import Path

from laya_cleanup_experiment import (
    QUESTION,
    corpus,
    deployment_assessment,
    development_candidate,
    metrics,
    validate_splits,
)


def head_corpus():
    data = corpus()
    fixture = Path(__file__).parent / "fixtures/laya_cleanup_head_final.json"
    data["final"] = json.loads(fixture.read_text())["cases"]
    validate_splits(data)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=160)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    args = parser.parse_args()
    if not 1 <= args.steps <= 400 or not 1 <= len(args.seeds) <= 3:
        parser.error("Bounded experiment requires 1–400 steps and 1–3 seeds")

    # Lazy native imports: the data/evaluation contracts stay portable on CI.
    import mlx.core as mx
    import mlx.nn as nn
    import mlx.optimizers as opt
    import numpy as np
    from laya_mlx.agent import collate_items
    from laya_mlx.model import DecisionHead
    from laya_research_base import load_research_base
    from mlx.utils import tree_flatten, tree_unflatten

    from jev_clean.infrastructure.model import MODEL_ID, MODEL_REVISION

    data = head_corpus()
    out = args.output
    out.mkdir(mode=0o700, parents=True, exist_ok=True)
    (out / "corpus.json").write_text(json.dumps(data, indent=2))
    backend = load_research_base()
    started = time.perf_counter()
    features, masks, positions, gold, baseline = {}, {}, {}, {}, {}
    for split, rows in data.items():
        hidden, attention, marker_positions, labels, predictions = [], [], [], [], []
        for row in rows:
            items, _ = backend.prepare(row["state"], {"disposition": QUESTION})
            prefix, _ = backend.prepare("", {"disposition": QUESTION})
            if (
                len(prefix[0]["ids"]) + len(backend.tok(row["state"], add_special_tokens=False)["input_ids"])
                > backend.cfg["max_len"]
            ):
                raise ValueError("Experiment evidence exceeds native context")
            batch = collate_items(items, backend.tok.pad_token_id)
            tensors = {k: mx.array(v) for k, v in batch.items()}
            h = backend.model.encoder(tensors["input_ids"], tensors["attention_mask"])
            h += backend.model.type_emb(tensors["qtype"])[:, None, :]
            mx.eval(h)
            hidden.append(np.array(h[0], dtype=np.float32))
            attention.append(np.array(tensors["attention_mask"][0]))
            marker_positions.append(np.array(tensors["marker_pos"][0]))
            labels.append(row["label"])
            logits, _ = backend.forward(batch)
            predictions.append(int(np.array(logits)[0].argmax()))
        longest = max(len(h) for h in hidden)
        dims = hidden[0].shape[-1]
        xf = np.zeros((len(hidden), longest, dims), dtype=np.float32)
        mask = np.zeros((len(hidden), longest), dtype=bool)
        for i, h in enumerate(hidden):
            xf[i, : len(h)] = h
            mask[i, : len(h)] = attention[i]
        features[split] = mx.array(xf)
        masks[split] = mx.array(mask)
        positions[split] = mx.array(np.stack(marker_positions))
        gold[split] = labels
        baseline[split] = metrics(labels, predictions)
        print("BASE", split, baseline[split], flush=True)

    class Readout(nn.Module):
        def __init__(self):
            super().__init__()
            dims = backend.encoder_cfg["hidden_size"]
            self.head = DecisionHead(dims, backend.cfg["head_layers"])
            self.scorer = nn.Sequential(
                nn.LayerNorm(dims), nn.Linear(dims, dims), nn.GELU(), nn.Linear(dims, 1)
            )
            weights = {
                **{
                    "head." + k: v.astype(mx.float32)
                    for k, v in tree_flatten(backend.model.head.parameters())
                },
                **{
                    "scorer." + k: v.astype(mx.float32)
                    for k, v in tree_flatten(backend.model.scorer.parameters())
                },
            }
            self.update(tree_unflatten(weights.items()))

        def __call__(self, x, mask, pos):
            h = self.head(x, mask[:, None, None, :])
            markers = h[mx.arange(h.shape[0])[:, None], pos]
            return self.scorer(markers).squeeze(-1)

    runs = []
    for seed in args.seeds:
        mx.random.seed(seed)
        rng = random.Random(seed)
        model = Readout()
        optimizer = opt.AdamW(learning_rate=2e-5, weight_decay=0.01)

        def loss_fn(model, x, mask, pos, y):
            return nn.losses.cross_entropy(model(x, mask, pos), y, reduction="mean")

        gradient = nn.value_and_grad(model, loss_fn)
        best, best_weights, best_step = None, None, 0
        t = time.perf_counter()
        for step in range(1, args.steps + 1):
            indices = rng.sample(range(len(gold["train"])), 4)
            ix = mx.array(indices)
            y = mx.array([gold["train"][i] for i in indices])
            loss, gradients = gradient(
                model, features["train"][ix], masks["train"][ix], positions["train"][ix], y
            )
            optimizer.update(model, gradients)
            mx.eval(model.parameters(), optimizer.state, loss)
            if step % 20 == 0 or step == args.steps:
                logits = model(features["dev"], masks["dev"], positions["dev"])
                mx.eval(logits)
                dev = metrics(gold["dev"], np.array(logits).argmax(axis=1).tolist())
                rank = (dev["false_remove"], -dev["correct"])
                if best is None or rank < best:
                    best, best_step = rank, step
                    best_weights = {k: mx.array(v) for k, v in tree_flatten(model.parameters())}
                    mx.eval(best_weights)
                print("STEP", seed, step, "loss", round(float(loss), 4), "DEV", dev, flush=True)
        model.update(tree_unflatten(best_weights.items()))
        report = {
            "seed": seed,
            "selected_step": best_step,
            "train_seconds": round(time.perf_counter() - t, 3),
        }
        for split in data:
            logits = model(features[split], masks[split], positions[split])
            mx.eval(logits)
            predicted = np.array(logits).argmax(axis=1).tolist()
            report[split] = metrics(gold[split], predicted)
            report[split + "_rows"] = [
                {"family": r["family"], "expected": r["label"], "predicted": p}
                for r, p in zip(data[split], predicted, strict=True)
            ]
        mx.save_safetensors(str(out / f"head-seed-{seed}.safetensors"), best_weights)
        runs.append(report)
        print("RESULT", json.dumps({k: v for k, v in report.items() if not k.endswith("_rows")}), flush=True)
    selected = development_candidate(runs)
    result = {
        "base_model": MODEL_ID,
        "base_revision": MODEL_REVISION,
        "question": QUESTION,
        "baseline": baseline,
        "runs": runs,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "selected_seed_by_dev": selected["seed"],
        "assessment": deployment_assessment(baseline["final"], selected["final"]),
        "recipe": "Original Laya head/scorer trained float32; encoder/type embeddings frozen; microbatch 4, 2e-5 AdamW, checkpoint/seed selected on dev only. Earlier test exposed after scorer run; final 24 families authored/frozen before head run, now exposed. Not RLCD/full fine-tune. Richer synthetic evidence is not production filesystem ground truth. No permission gates/calibration thresholds in raw metrics. No installed changes or guarantee of safe deletion.",
    }
    (out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    for path in out.iterdir():
        if path.is_file():
            path.chmod(0o600)


if __name__ == "__main__":
    main()
