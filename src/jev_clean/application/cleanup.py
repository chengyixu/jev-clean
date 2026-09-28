"""Model-prioritized concrete directory inventory, then model assessment of measured files."""

import time
from collections import Counter
from pathlib import Path

from jev_clean.domain.models import DiskNode, ExplorationResult, ExplorationStep
from jev_clean.domain.policy import ROOTS, apply_policy
from jev_clean.infrastructure import native
from jev_clean.infrastructure.scanner import no_symlink_ancestors, scan_candidates


def investigate_cleanup(
    home: Path,
    advisor,
    *,
    roots: list[Path] | None = None,
    open_paths: set[str] | None,
    max_nodes: int = 6,
    max_candidates: int = 600,
    seconds: float = 120,
    progress=lambda _: None,
    cancelled=lambda: False,
) -> ExplorationResult:
    result = ExplorationResult()
    paths = (
        roots
        if roots is not None
        else [home / r for r, _, _ in ROOTS] + [home / ".cache", home / "Library/Application Support"]
    )
    paths = list(dict.fromkeys(p for p in paths if p.is_dir() and no_symlink_ancestors(p)))
    pending = [DiskNode(str(p), None, True, 0, False) for p in paths]
    result.nodes.extend(pending)
    stats: dict = {
        "observed_files": 0,
        "protected_files": 0,
        "model_assessed": 0,
        "model_kept": 0,
        "model_review": 0,
        "model_remove": 0,
        "approved": 0,
    }
    reasons: Counter[str] = Counter()
    seen: set[str] = set()
    started = time.monotonic()
    while (
        pending and len(result.steps) < max_nodes and time.monotonic() - started < seconds and not cancelled()
    ):
        choices = pending[:6]
        decision = advisor.choose_directory(choices, "clean")
        selected = int(decision.choice.removeprefix("n"))
        if not 0 <= selected < len(choices):
            raise ValueError("Model selected an unavailable directory")
        node = choices[selected]
        pending.remove(node)
        node.decision = decision
        progress(f"Laya chose {node.path.replace(str(home), '~', 1)}")
        remaining = max(0.1, seconds - (time.monotonic() - started))
        measurements = native.measure_tree(
            Path(node.path), timeout=min(8, remaining), progress=progress, cancelled=cancelled
        )
        own = next(m for m in measurements if m.path == node.path)
        node.allocated_bytes = own.allocated_bytes
        node.complete = own.complete
        observation = scan_candidates(
            home,
            open_paths=open_paths,
            directories=[Path(node.path)],
            require_full_scope=False,
            max_files=50000,
            seconds=min(20, remaining),
            progress=progress,
            cancelled=cancelled,
        )
        if not observation.complete:
            result.complete = False
            result.warnings.extend(observation.warnings)
        new = [c for c in observation.candidates if c.path not in seen]
        seen.update(c.path for c in new)
        stats["observed_files"] += len(new)
        eligible = []
        for item in new:
            if item.eligible:
                eligible.append(item)
            else:
                stats["protected_files"] += 1
                reasons[item.reason] += 1
        progress(f"{len(new)} files observed · {len(eligible)} pass metadata checks")
        for item in eligible:
            if (
                cancelled()
                or stats["model_assessed"] >= max_candidates
                or time.monotonic() - started >= seconds
            ):
                result.complete = False
                result.warnings.append("File assessment budget reached; unassessed files are not approved")
                break
            proposal = advisor.predict(item)
            checked = apply_policy(item, proposal)
            result.candidates.append(checked)
            stats["model_assessed"] += 1
            stats["model_" + ("kept" if proposal.choice == "keep" else proposal.choice)] += 1
            stats["approved"] += int(checked.selectable)
            progress(
                f"Laya {proposal.choice} · {item.allocated_bytes / 10**6:.2f} MB · {max(proposal.probabilities.values()):.0%}"
            )
        result.steps.append(ExplorationStep(node.path, decision, len(new)))
        if stats["model_assessed"] >= max_candidates:
            break
    if pending or cancelled():
        result.complete = False
        result.warnings.append("Investigation bounded; remaining locations are unassessed")
    stats["guard_reasons"] = dict(reasons)
    stats["directories_inspected"] = len(result.steps)
    stats["remaining_directories"] = len(pending)
    stats["open_file_check_available"] = open_paths is not None
    result.stats = stats
    return result
