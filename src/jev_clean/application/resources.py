"""Resource-level model assessment over native parallel measurements, not per-file AI."""

from __future__ import annotations

import threading
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import replace
from pathlib import Path
from typing import Any

from jev_clean.domain.models import (
    Candidate,
    DiskNode,
    ExplorationResult,
    ExplorationStep,
    human_bytes,
    ordered_candidates,
)
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.decision_cache import DecisionCache
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.model import state_for
from jev_clean.infrastructure.resources import discover_resources, measure_resource
from jev_clean.infrastructure.volumes import DiskScope, startup_scope


def investigate_resources(
    home: Path,
    advisor,
    mode: str,
    *,
    roots: list[Path] | None = None,
    state_dir: Path | None = None,
    open_paths: set[str] | None = None,
    deep: bool = False,
    progress=lambda _: None,
    cancelled=lambda: False,
) -> ExplorationResult:
    if mode not in ("clean", "status"):
        raise ValueError("Unknown mode")
    started = time.monotonic()
    scope = startup_scope() if roots is None else DiskScope(roots, kind="custom")
    progress("Resource inventory: native measurements; model judges resources, not every child file.")
    frontier = discover_resources(home, scope, cancelled)
    evidence = EvidenceCollector(home)
    evidence.application_metadata()  # Freeze one read-only manifest snapshot before worker threads.
    result = ExplorationResult()
    stats: dict[str, Any] = {
        "scope": scope.kind,
        "resources_discovered": len(frontier.paths),
        "resources_measured": 0,
        "model_assessed_resources": 0,
        "fresh_model_inferences": 0,
        "reused_model_decisions": 0,
        "approved": 0,
        "approved_candidate_bytes": 0,
        "review_candidate_bytes": 0,
        "model_remove": 0,
        "model_review": 0,
        "model_kept": 0,
        "execution_unavailable": 0,
        "measurement_gaps": 0,
        "walk_finished": False,
        "granularity": "resource",
    }
    state_dir = state_dir or home / ".local/state/jev-clean/resource-scan"
    stop = threading.Event()

    def stopped():
        return stop.is_set() or cancelled()

    with DecisionCache(state_dir, advisor, scope.roots, mode) as cache:
        pending_roots = [DiskNode(str(p), None, True, 0, False) for p in scope.roots]
        # Mandatory model prioritization; every root remains in the declared inventory.
        preferred = []
        while pending_roots and not stopped():
            options = pending_roots[:6]
            decision = advisor.choose_directory(options, mode)
            index = int(decision.choice.removeprefix("n"))
            if not 0 <= index < len(options):
                raise ValueError("Model selected an unavailable resource root")
            chosen = pending_roots.pop(index)
            preferred.append(Path(chosen.path))
            result.steps.append(ExplorationStep(chosen.path, decision, 0))
        priority = {p: i for i, p in enumerate(preferred)}
        paths = sorted(
            frontier.paths,
            key=lambda p: (
                min((i for root, i in priority.items() if p.is_relative_to(root)), default=len(priority)),
                str(p),
            ),
        )
        iterator = iter(paths)
        with ThreadPoolExecutor(max_workers=4) as workers:
            active: dict[Future[Candidate], Path] = {}

            def fill():
                while len(active) < 4 and not stopped():
                    path = next(iterator, None)
                    if path is None:
                        break
                    future = workers.submit(
                        measure_resource, path, home, evidence, open_paths, deep=deep, cancelled=stopped
                    )
                    active[future] = path

            fill()
            try:
                while active and not stopped():
                    done, _ = wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                    for future in done:
                        if stopped():
                            break
                        path = active.pop(future)
                        try:
                            item = future.result()
                        except (OSError, ValueError) as error:
                            stats["measurement_gaps"] += 1
                            result.warnings.append(f"Measurement unavailable: {path}: {error}")
                            continue
                        stats["resources_measured"] += 1
                        stats["measurement_gaps"] += int(not item.scan_complete)
                        state = state_for(item)
                        decision = cache.get(state)
                        if decision is None:
                            decision = advisor.predict(item)
                            cache.put(state, decision)
                            stats["fresh_model_inferences"] += 1
                        else:
                            decision = replace(decision, reused=True, elapsed_ms=0.0)
                            stats["reused_model_decisions"] += 1
                        stats["model_assessed_resources"] += 1
                        stats["model_" + ("kept" if decision.choice == "keep" else decision.choice)] += 1
                        reviewed = apply_policy(item, decision)
                        stats["execution_unavailable"] += int(not reviewed.eligible)
                        if mode == "clean" and decision.choice in ("remove", "review"):
                            result.candidates.append(reviewed)
                            if reviewed.selectable:
                                stats["approved"] += 1
                                stats["approved_candidate_bytes"] += item.allocated_bytes
                            elif decision.choice == "review":
                                stats["review_candidate_bytes"] += item.allocated_bytes
                        result.nodes.append(
                            DiskNode(
                                str(path),
                                item.allocated_bytes if item.scan_complete else None,
                                item.unit == "directory",
                                0,
                                item.scan_complete,
                            )
                        )
                        # Progress is a cleanup-facing observation, not a license
                        # to advertise unsupported raw model errors as garbage.
                        progress(
                            f"{'Candidate' if reviewed.selectable else 'Measured'} · {human_bytes(item.allocated_bytes)} · {path}"
                        )
                        cache.save_progress(stats, False)
                    fill()
            finally:
                stop.set()
                for future in active:
                    future.cancel()
        stats["walk_finished"] = not cancelled() and stats["resources_measured"] + len(
            result.warnings
        ) == len(paths)
        stats["elapsed_seconds"] = round(time.monotonic() - started, 3)
        stats["model_assessed"] = stats["model_assessed_resources"]
        result.complete = bool(
            stats["walk_finished"]
            and not stats["measurement_gaps"]
            and not frontier.issues
            and not scope.exclusions
        )
        stats["coverage"] = {
            "scope": scope.kind,
            "granularity": "resource",
            "requested_roots": list(map(str, scope.roots)),
            "complete": result.complete,
            "scope_finished": stats["walk_finished"],
            "resources_discovered": len(paths),
            "resources_measured": stats["resources_measured"],
            "symlinks_observed": frontier.symlinks,
            "aliases_deduplicated": frontier.aliases,
            "issues": frontier.issues,
            "exclusions": scope.exclusions,
            "model_reuse": "Exact resource evidence/question/model cache. No individual child-file inference claim.",
            "resource_membership": "Native subtree totals; exact metadata manifests prepared only for selected review.",
            "measurement_deadline_seconds": 30,
            "measurement_workers": 4,
        }
        cache.save_progress(stats, bool(stats["walk_finished"]))
    if not result.complete:
        result.warnings.append("Resource inventory has explicit gaps/exclusions; no full-access claim.")
    if cancelled():
        result.candidates = [
            apply_policy(replace(c, scan_complete=False), c.decision) for c in result.candidates
        ]
    result.candidates = ordered_candidates(result.candidates)
    result.nodes.sort(key=lambda n: (-(n.allocated_bytes or 0), n.path))
    result.stats = stats
    return result
