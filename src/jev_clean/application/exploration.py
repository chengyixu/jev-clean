"""Model-directed bounded exploration. The model, not a directory rule, chooses expansion."""

from __future__ import annotations

import os
import stat
import time
from collections import deque
from pathlib import Path
from typing import Callable

from jev_clean.domain.models import DiskNode, ExplorationResult, ExplorationStep
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure import native
from jev_clean.infrastructure.scanner import candidate_from_stat, no_symlink_ancestors


def inspect_children(node: DiskNode, *, limit: int = 200) -> tuple[list[DiskNode], bool]:
    """Shallow no-follow listing, with bounded directory measurements. Never file contents."""
    path = Path(node.path)
    if not no_symlink_ancestors(path):
        return [], False
    device = path.stat().st_dev
    children: list[DiskNode] = []
    complete = True
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if len(children) >= limit:
                    complete = False
                    break
                try:
                    st = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(st.st_mode) or st.st_dev != device:
                        continue
                    if not (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)):
                        continue
                    children.append(
                        DiskNode(
                            entry.path,
                            None if entry.is_dir(follow_symlinks=False) else st.st_blocks * 512,
                            entry.is_dir(follow_symlinks=False),
                            node.depth + 1,
                            True,
                            max(0, (time.time() - st.st_mtime) / 86400),
                        )
                    )
                except OSError:
                    complete = False
    except OSError:
        return [], False
    return children, complete


def explore(
    roots: list[DiskNode],
    advisor,
    mode: str,
    *,
    home: Path | None = None,
    open_paths: set[str] | None = None,
    max_nodes: int = 60,
    max_depth: int = 5,
    max_candidates: int = 160,
    seconds: float = 100,
    progress: Callable[[str], None] = lambda _: None,
    cancelled: Callable[[], bool] = lambda: False,
    child_reader=inspect_children,
) -> ExplorationResult:
    result = ExplorationResult(nodes=list(roots))
    queue = deque(roots)
    visited: set[str] = set()
    started = time.monotonic()
    steps = 0
    model_calls = 0
    while queue and steps < max_nodes and time.monotonic() - started < seconds and not cancelled():
        node = queue.popleft()
        if node.path in visited or not node.is_dir:
            continue
        visited.add(node.path)
        decision = advisor.inspect(node, mode)
        model_calls += 1
        node.decision = decision
        steps += 1
        progress(
            f"Laya explorer → {Path(node.path).name} → {decision.choice.upper()} "
            f"{max(decision.probabilities.values()):.0%} · {decision.elapsed_ms:.1f} ms"
        )
        children: list[DiskNode] = []
        if decision.choice == "inspect" and node.depth < max_depth:
            if node.allocated_bytes is None:
                measured = native.measure(Path(node.path), timeout=8)
                node.allocated_bytes = measured.allocated_bytes
                node.complete = measured.complete
            children, complete = child_reader(node)
            if not complete:
                result.complete = False
                result.warnings.append(f"Partial directory inventory: {node.path}")
            for child in children:
                if cancelled() or model_calls >= 200 or time.monotonic() - started >= seconds:
                    result.complete = False
                    result.warnings.append("Model exploration budget reached; remaining items unassessed")
                    break
                # Every displayed purpose is a model classification, never inferred by the UI.
                child.purpose = advisor.classify(child)
                model_calls += 1
                if child.is_dir:
                    queue.append(child)
                elif mode == "clean" and home and len(result.candidates) < max_candidates and complete:
                    try:
                        st = Path(child.path).lstat()
                        item = candidate_from_stat(Path(child.path), st, home, open_paths)
                        proposed = advisor.predict(item)
                        model_calls += 1
                        item = apply_policy(item, proposed)
                        result.candidates.append(item)
                        progress(
                            f"Laya file → {proposed.choice.upper()} {max(proposed.probabilities.values()):.0%} "
                            f"· {proposed.elapsed_ms:.1f} ms · guard {'PASS' if item.eligible else 'VETO'}"
                        )
                    except OSError:
                        result.warnings.append(f"Changed/unreadable file: {child.path}")
                        result.complete = False
            result.nodes.extend(children)
        result.steps.append(ExplorationStep(node.path, decision, len(children)))
        if model_calls >= 200:
            break
    if queue or cancelled():
        result.complete = False
        result.warnings.append(
            "Exploration budget/depth/cancellation boundary reached; undiscovered data is not zero. Narrow roots and rescan for more detail."
        )
    return result
