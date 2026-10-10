"""Research evaluation using the EXACT production observation/ensemble contract.

This script loads candidate weights only in its own process; it never installs a
model, calls cleanup, or replaces shared application files. No policy gates in
raw model metrics. Observation/ensemble logic lives in one runtime definition.
"""

import argparse
import json
from pathlib import Path

from jev_clean.infrastructure.learned_cleanup import (
    LABELS,
    QUESTION,
    ensemble_predict,
)
from jev_clean.infrastructure.learned_cleanup import (
    observed_state as observed_state,
)


def load_candidate(path):
    """Load research weights in this isolated evaluation process, not an installation."""
    import mlx.core as mx
    from mlx.utils import tree_unflatten

    from jev_clean.infrastructure.model import LayaAdvisor

    advisor = LayaAdvisor()
    advisor.load()
    backend = advisor._shared
    weights = mx.load(str(path))
    if not isinstance(weights, dict):
        raise ValueError("Candidate must contain named weight tensors")
    backend.model.update(tree_unflatten([(k, v.astype(mx.float16)) for k, v in weights.items()]))
    mx.eval(backend.model.parameters())
    return backend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from laya_cleanup_experiment import metrics

    backend = load_candidate(args.adapter)
    rows = json.loads(args.cases.read_text())["cases"]
    predictions, results = [], []
    for row in rows:
        answer = ensemble_predict(backend, row["state"])
        predictions.append(LABELS.index(answer["choice"]))
        results.append({"family": row["family"], "expected": row["label"], **answer})
    report = {
        "metrics": metrics([r["label"] for r in rows], predictions),
        "rows": results,
        "question": QUESTION,
        "limits": "Authored synthetic evidence, learned Laya only. No installed update or runtime permission gates. Inherited temperatures are not calibrated deletion-safety confidence.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    args.output.chmod(0o600)
    print(json.dumps(report["metrics"], indent=2))


if __name__ == "__main__":
    main()
