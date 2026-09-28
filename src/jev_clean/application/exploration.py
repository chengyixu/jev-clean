"""Measured inventory first; mandatory model chooses the next concrete breakdown."""

from __future__ import annotations

import os
import stat
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from jev_clean.domain.models import DiskNode, ExplorationResult, ExplorationStep
from jev_clean.infrastructure import native
from jev_clean.infrastructure.scanner import no_symlink_ancestors


def inspect_children(node: DiskNode, *, limit: int = 1000) -> tuple[list[DiskNode], bool]:
    path = Path(node.path)
    if not no_symlink_ancestors(path):
        return [], False
    children: list[DiskNode] = []
    complete = True
    try:
        device = path.stat().st_dev
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
                    directory = stat.S_ISDIR(st.st_mode)
                    children.append(
                        DiskNode(
                            entry.path,
                            None if directory else st.st_blocks * 512,
                            directory,
                            node.depth + 1,
                            not directory,
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
    max_nodes: int = 8,
    max_depth: int = 4,
    max_candidates: int = 160,
    seconds: float = 150,
    deep: bool = False,
    progress=lambda _: None,
    cancelled=lambda: False,
    child_reader=inspect_children,
) -> ExplorationResult:
    result = ExplorationResult(nodes=list(roots))
    nodes = {n.path: n for n in roots}
    started = time.monotonic()
    observed: dict[str, list] = {}

    def inventory(node):
        if home is not None and Path(node.path) == home:
            return native.measure_children(
                home, timeout=min(60, seconds), progress=progress, cancelled=cancelled
            )
        return native.measure_tree(
            Path(node.path), timeout=min(60, seconds), deep=deep, progress=progress, cancelled=cancelled
        )

    # The model requires facts to choose useful reads. Native inventory itself is not a cleanup decision.
    with ThreadPoolExecutor(max_workers=min(4, max(1, len(roots)))) as pool:
        pending = {pool.submit(inventory, n): n for n in roots}
        for future in as_completed(pending):
            root = pending[future]
            measurements = future.result()
            observed[root.path] = measurements
            for m in measurements:
                if m.path in nodes:
                    node = nodes[m.path]
                    node.allocated_bytes = m.allocated_bytes
                    node.complete = m.complete
                else:
                    node = DiskNode(
                        m.path, m.allocated_bytes, Path(m.path).is_dir(), root.depth + 1, m.complete
                    )
                    nodes[m.path] = node
            if not all(m.complete for m in measurements):
                result.complete = False
                result.warnings.append("Partial native inventory: " + root.path)
    queue = list(roots)
    visited = set()
    while (
        queue and len(result.steps) < max_nodes and time.monotonic() - started < seconds and not cancelled()
    ):
        choices = queue[:6]
        decision = advisor.choose_directory(choices, mode)
        index = int(decision.choice.removeprefix("n"))
        if not 0 <= index < len(choices):
            raise ValueError("Model chose an unavailable directory")
        node = choices[index]
        queue.remove(node)
        if node.path in visited:
            continue
        visited.add(node.path)
        node.decision = decision
        node.purpose = advisor.classify(node)
        progress("Laya chose " + node.path)
        if node.path not in observed:
            left = max(0.1, seconds - (time.monotonic() - started))
            measurements = native.measure_tree(
                Path(node.path), timeout=min(20, left), deep=deep, progress=progress, cancelled=cancelled
            )
            observed[node.path] = measurements
            for m in measurements:
                if m.path in nodes:
                    nodes[m.path].allocated_bytes = m.allocated_bytes
                    nodes[m.path].complete = m.complete
                else:
                    nodes[m.path] = DiskNode(
                        m.path, m.allocated_bytes, Path(m.path).is_dir(), node.depth + 1, m.complete
                    )
        children, complete = child_reader(node)
        if not complete:
            result.complete = False
            result.warnings.append("Partial child listing: " + node.path)
        for child in children:
            existing = nodes.get(child.path)
            if existing is None:
                nodes[child.path] = child
            if (
                child.is_dir
                and child.depth < max_depth
                and child.path not in visited
                and not any(n.path == child.path for n in queue)
            ):
                queue.append(nodes[child.path])
        # Completed roots stay ahead; afterwards offer the largest observed branches to the model.
        queue.sort(key=lambda n: (n.depth, -(n.allocated_bytes or 0)))
        result.steps.append(ExplorationStep(node.path, decision, len(children)))
    if queue or cancelled():
        result.complete = False
        result.warnings.append("Further breakdown bounded; remaining directories are not fully investigated")
    result.nodes = list(nodes.values())
    result.stats = {
        "directories_inspected": len(result.steps),
        "measured_nodes": sum(n.allocated_bytes is not None for n in result.nodes),
        "remaining_directories": len(queue),
    }
    return result
