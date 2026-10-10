"""Path-free observed evidence and learned Laya probability ensemble.

No arbitrary path/name strings enter inference. Model probabilities alone choose
the class; no path/tag admission gate or confidence threshold here. Runtime uses pinned adapted Laya weights; confidence is not deletion-safety calibration.
"""

import itertools
import time

LABELS = ("remove", "review", "keep")
QUESTION = {
    "type": "choice",
    "instructions": "What does the observed evidence establish about the data in this resource?",
    "criteria": {
        "A": "The data is disposable and no longer needed.",
        "B": "Whether the data is needed is unknown or uncertain.",
        "C": "The data is needed and must be retained.",
    },
}


def _numeric_count(value, limit=256):
    return min(max(int(value), 0), limit) if str(value).isdigit() else None


def _extension_counts(value):
    """Only count + literal suffix tokens, never arbitrary basename sentences."""
    result = []
    for component in str(value).split(",")[:8]:
        suffix, sep, count = component.strip().rpartition(":")
        n = _numeric_count(count)
        if not sep or n is None or len(suffix) > 24:
            continue
        if (
            suffix == "[none]"
            or suffix.startswith(".")
            and all(c.isascii() and (c.isalnum() or c in "._-") for c in suffix)
        ):
            result.append(f"{suffix}:{n}")
    return ", ".join(result) or "unknown"


def structural_formats(evidence):
    """Human-readable format observations; not uniqueness or disposal conclusions."""
    files = _extension_counts(evidence.get("file_extensions", evidence.get("extension", "") + ":1"))
    directories = _extension_counts(evidence.get("directory_extensions", ""))
    suffixes = {s.strip().split(":", 1)[0] for s in (files + "," + directories).split(",")}
    formats = []
    if suffixes & {
        ".jpg",
        ".jpeg",
        ".heic",
        ".png",
        ".nef",
        ".cr3",
        ".mp4",
        ".mov",
        ".wav",
        ".mp3",
        ".photoslibrary",
    }:
        formats.append("media or photo-library formats; original-versus-preview status unknown")
    if suffixes & {".key", ".pem", ".p12", ".pfx", ".kdbx", ".wallet", ".credentials"}:
        formats.append("credential or recovery-related formats; real-versus-dummy status unknown")
    if suffixes & {
        ".py",
        ".swift",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".rs",
        ".go",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".kt",
        ".kts",
        ".rb",
        ".php",
        ".lua",
        ".vue",
        ".git",
        ".ipynb",
    }:
        formats.append("source or repository formats; original-versus-generated status unknown")
    if suffixes & {".db", ".sqlite", ".sqlite3", ".wal"}:
        formats.append("database formats; persistent-versus-generated cache role unknown")
    if suffixes & {".safetensors", ".gguf", ".raw", ".qcow2", ".dmg"}:
        formats.append("model or disk-image formats; dependencies and replacement availability unknown")
    return (
        "; ".join(formats)
        if formats
        else "no recognized user-data format in the bounded sample; not proof of subtree purity"
    )


def observed_state(item):
    """Canonical observation record, same path-renaming invariant in train/runtime."""
    if item.operation == "owner_prune":
        return item.action_evidence
    evidence = item.evidence
    entries = _numeric_count(evidence.get("sampled_entries", ""))
    scope = evidence.get("observation_scope")
    known_scopes = {
        "all immediate entries; descendants uninspected",
        "partial immediate-entry sample; no subtree purity claim",
    }
    namespace = evidence.get("storage_namespace")
    if namespace == "macos-cache":
        from jev_clean.infrastructure.evidence import CACHE_NAMESPACE_CONTRACT

        purpose = f"Actual filesystem namespace: macOS Library/Caches. {CACHE_NAMESPACE_CONTRACT} "
    elif namespace == "macos-diagnostic-log":
        from jev_clean.infrastructure.evidence import LOG_NAMESPACE_CONTRACT

        purpose = f"Actual filesystem namespace: macOS Library/Logs. {LOG_NAMESPACE_CONTRACT} "
    else:
        purpose = "Filesystem storage purpose is unverified. "
    declaration = (
        "A valid cache declaration from the owner indicates rebuildability; active references and current necessity remain unknown."
        if item.disposal is not None
        or evidence.get("disposal_basis") == "observed valid CACHEDIR.TAG cache declaration"
        else "No generating-owner data-role declaration was observed."
    )
    activity = (
        "An active process is observed using this resource."
        if item.open_file is True
        else "No open handle was observed; this does not establish absence of future dependencies."
        if item.open_file is False
        else "Active process use is unknown."
    )
    return (
        "Observed resource. Proposed operation: move the entire resource to Trash. "
        f"Immediate entries sampled: {entries if entries is not None else 'unknown'}. "
        f"File extension observations: {_extension_counts(evidence.get('file_extensions', evidence.get('extension', '') + ':1'))}. "
        f"Directory extension observations: {_extension_counts(evidence.get('directory_extensions', ''))}. "
        f"Observation scope: {scope if scope in known_scopes else 'unknown; descendants uninspected'}. "
        f"Structural formats: {structural_formats(evidence)}. "
        f"{purpose}{declaration} {activity} "
        "Actual contents, unique originals and owner retention wishes are not inferred from placement. "
        "The user's requested cleanup concerns the selected resource, not arbitrary personal folders. "
        f"Size is measured separately for display, not evidence of disposability. Exact measurement {'complete' if item.scan_complete else 'incomplete'}."
    )


def ensemble_predict(backend, state, *, orders=None):
    """Option-permutation probability ensemble; outputs are raw learned judgments."""
    import numpy as np
    from laya_mlx.agent import collate_items
    from laya_mlx.common import build_sequence, temp_bucket

    orders = list(itertools.permutations(range(3))) if orders is None else orders
    if not orders:
        raise ValueError("Empty option ensemble")
    items = []
    q = backend._to_internal(QUESTION)
    prefix, _ = backend.prepare("", {"disposition": QUESTION})
    if (
        len(prefix[0]["ids"]) + len(backend.tok(state, add_special_tokens=False)["input_ids"])
        > backend.cfg["max_len"]
    ):
        raise ValueError("Observation record exceeds native Laya context")
    for order in orders:
        if sorted(order) != [0, 1, 2]:
            raise ValueError("Invalid option permutation")
        ids, markers = build_sequence(
            backend.tok,
            state,
            q,
            backend.cfg["max_len"],
            backend.cfg["head_max_len"],
            option_order=list(order),
        )
        items.append({"ids": ids, "markers": markers, "qtype": 0})
    t = time.perf_counter()
    logits, _ = backend.forward(collate_items(items, backend.tok.pad_token_id))
    z = np.array(logits)
    if z.shape != (len(orders), 3) or not np.isfinite(z).all():
        raise ValueError("Invalid/nonfinite learned model logits")
    scale = backend.temperature_by_options.get(temp_bucket(0, 3), backend.temperature[0])
    z /= scale
    z -= z.max(axis=1, keepdims=True)
    p = np.exp(z)
    p /= p.sum(axis=1, keepdims=True)
    mapped = np.zeros_like(p)
    for i, order in enumerate(orders):
        for j, label in enumerate(order):
            mapped[i, label] = p[i, j]
    distribution = mapped.mean(axis=0)
    return {
        "choice": LABELS[int(distribution.argmax())],
        "probabilities": {k: float(v) for k, v in zip(LABELS, distribution, strict=True)},
        "elapsed_ms": (time.perf_counter() - t) * 1000,
        "order_choices": [LABELS[i] for i in mapped.argmax(axis=1).tolist()],
    }


def predict_cleanup(backend, item):
    from jev_clean.domain.models import Decision

    result = ensemble_predict(backend, observed_state(item))
    return Decision(
        result["choice"],
        result["probabilities"],
        "local Laya cleanup encoder adaptation",
        result["elapsed_ms"],
    )
