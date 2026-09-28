"""Mandatory-model workflows shared by TUI and agent skill: Clean and Status only."""

from __future__ import annotations

import os
import time
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from jev_clean.application.whole_disk import investigate_disk
from jev_clean.domain.models import (
    AuditReport,
    Candidate,
    CategoryReport,
    DiskNode,
    Fingerprint,
    Measurement,
    ScanReport,
)
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure import native
from jev_clean.infrastructure.model import LayaAdvisor
from jev_clean.infrastructure.trash import read_private, save_private


def demo_report(home: Path, mode: str, advisor: LayaAdvisor, progress: Callable[[str], None]) -> AuditReport:
    """Synthetic FILE METADATA, real model exploration/classification/removal decisions."""
    specs = [
        ("Library/Caches/demo.builder/old-artifact", "user-cache", 840_000_000, 72, False),
        ("Library/Logs/demo.editor/render.log.4", "rotated-log", 125_000_000, 42, False),
        ("Library/Caches/demo.browser/active-cache", "user-cache", 310_000_000, 1, True),
        ("Library/Caches/demo.app/history.sqlite", "database", 950_000_000, 90, False),
        ("Library/Caches/demo.pipeline/unknown-blob", "unknown", 62_000_000, 61, False),
    ]
    candidates = []
    nodes = []
    steps = []
    remaining = list(enumerate(specs))
    while remaining:
        options = [DiskNode(str(home / Path(s[0]).parent), s[2], True, 1) for _, s in remaining]
        choice = advisor.choose_directory(options, mode)
        position = int(choice.choice.removeprefix("n"))
        if not 0 <= position < len(remaining):
            raise ValueError("Model selected an unavailable demo directory")
        i, (path, kind, size, age, active) = remaining.pop(position)
        node = options[position]
        node.decision = choice
        node.purpose = advisor.classify(node)
        nodes.append(asdict(node))
        steps.append(
            {
                "path": node.path,
                "decision": asdict(node.decision),
                "children_seen": 1,
            }
        )
        progress(
            f"Laya explorer → {Path(path).parent.name} → {node.decision.choice} · {node.decision.elapsed_ms:.1f} ms"
        )
        if mode == "clean":
            item = Candidate(
                str(i),
                str(home / path),
                kind,
                size,
                age * 86400,
                Fingerprint(1, i + 1, size, 0, 0, os.getuid(), 1),
                True,
                False,
                True,
                active,
            )
            proposed = advisor.predict(item)
            candidates.append(apply_policy(item, proposed))
            progress(
                f"Laya → {proposed.choice.upper()} {max(proposed.probabilities.values()):.0%} · {proposed.elapsed_ms:.1f} ms"
            )
    return AuditReport(
        1,
        datetime.now(timezone.utc).isoformat(),
        str(home),
        mode,
        ScanReport(candidates, files_seen=len(specs)),
        [Measurement("Synthetic cache inventory", 1_212_000_000, True, "Fixture; not your disk")],
        categories=CategoryReport(
            "2026-01-01 00:00:00.000 (DEMO)",
            500 * 10**9,
            20 * 10**9,
            {"com.apple.STMExtension.Documents": 200 * 10**9},
            280 * 10**9,
            source="Synthetic category arithmetic; not your Mac",
        ),
        diagnostics={
            "disk_total": 10**12,
            "disk_free": 190 * 10**9,
            "memory_percent": 54,
            "cpu_percent": 12,
            "swap_used": 2 * 10**9,
            "coverage": "Synthetic file metadata; real inference; no filesystem changes",
        },
        model_status=f"REAL Laya-MLX · load {advisor.load_ms:.0f} ms · synthetic file metadata",
        demo=True,
        exploration={"nodes": nodes, "steps": steps, "complete": True, "warnings": []},
    )


def audit(
    home: Path,
    mode: str,
    *,
    deep: bool = False,
    demo: bool = False,
    progress: Callable[[str], None] = lambda _: None,
    cancelled: Callable[[], bool] = lambda: False,
    roots: list[Path] | None = None,
) -> AuditReport:
    if mode not in ("clean", "status"):
        raise ValueError("Unknown mode: choose clean or status")
    progress("Loading model…")
    progress("Inspecting System Data…" if mode == "clean" else "Reading disk usage…")
    advisor = LayaAdvisor()
    advisor.load()  # Must succeed before native scans or synthetic demonstration.
    if demo:
        return demo_report(home, mode, advisor, progress)
    report = AuditReport(1, datetime.now(timezone.utc).isoformat(), str(home), mode, ScanReport())
    home = Path(os.path.abspath(home))
    for root in roots or []:
        if not root.is_absolute() or ".." in root.parts:
            raise ValueError("Explicit read scope must be an absolute filesystem path")
    handles = native.open_files(deep=True) if deep else native.open_files()
    report.diagnostics = native.status_snapshot(home)
    report.diagnostics["coverage"] = (
        "deep native diagnostics requested" if deep else "unprivileged; permission gaps reported"
    )
    # Native totals provide grounding, not exploration decisions.
    if __import__("platform").system() == "Darwin":
        for name in ["categories", "snapshots"]:
            progress(f"Grounding: {name}")
            if deep:
                evidence = native.deep_probe(name)
            else:
                code, out, err = native.run(native.DEEP_COMMANDS[name], 15)
                evidence = {"stdout": out, "stderr": err, "complete": code == 0, "returncode": code}
            if name == "categories":
                report.categories = (
                    native.parse_categories(evidence["stdout"]) if evidence["complete"] else None
                )
                report.diagnostics["category_probe"] = {k: v for k, v in evidence.items() if k != "stdout"}
            else:
                report.diagnostics[name] = evidence
    result = investigate_disk(
        home,
        advisor,
        mode,
        roots=roots,
        deep=deep,
        open_paths=handles,
        progress=progress,
        cancelled=cancelled,
    )
    report.created_at = datetime.now(
        timezone.utc
    ).isoformat()  # review expiry starts after a potentially long scan
    report.coverage = result.stats.get("coverage", {})
    report.exploration = {
        "nodes": [asdict(n) for n in result.nodes],
        "steps": [asdict(s) for s in result.steps],
        "warnings": result.warnings,
        "complete": result.complete,
        "stats": result.stats,
    }
    report.measurements = [
        Measurement(
            n.path, n.allocated_bytes, n.complete, "Model-selected breakdown; nested rows overlap, do not sum"
        )
        for n in result.nodes
        if n.is_dir
    ]
    report.scan = ScanReport(
        result.candidates, True, result.warnings, result.stats.get("observed_files", len(result.candidates))
    )
    report.model_status = (
        f"Mandatory local Laya-MLX · {result.stats.get('model_assessed_files', 0):,} files assessed · "
        f"{result.stats.get('fresh_model_inferences', 0):,} fresh / {result.stats.get('reused_model_decisions', 0):,} exact-input reused · "
        f"{result.stats.get('directory_model_decisions', 0):,} directory classifications"
    )
    if mode == "clean" and handles is None:
        report.scan.warnings.append("Open-file status unavailable: all removal candidates vetoed")
    if cancelled():
        report.scan.complete = False
        report.scan.candidates = [
            apply_policy(replace(c, scan_complete=False), c.decision) for c in report.scan.candidates
        ]
        report.scan.warnings.append("Cancelled; run a new operation before cleanup")
    return report


def reassess_selection(items: list[Candidate]) -> list[Candidate]:
    advisor = LayaAdvisor()
    advisor.load()
    assessed = [apply_policy(item, advisor.predict(item)) for item in items]
    if not all(c.selectable for c in assessed):
        raise ValueError("Model or safety gate withheld approval on recheck; rescan and review")
    return assessed


def save_plan(path: Path, report: AuditReport) -> None:
    save_private(path, report.to_dict())


def load_plan(path: Path, home: Path) -> list[Candidate]:
    data = read_private(path)
    if data.get("demo"):
        raise ValueError("Demo plans cannot change files")
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported schema")
    if data.get("home") != str(home):
        raise ValueError("Home mismatch; plan belongs to another root")
    age = time.time() - datetime.fromisoformat(data["created_at"]).timestamp()
    if not 0 <= age <= 3600:
        raise ValueError("Expired/future plan; rescan (plans last one hour)")
    if not data["scan"]["complete"]:
        raise ValueError("Partial file metadata cannot authorize cleanup")
    return [Candidate.from_dict(c) for c in data["scan"]["candidates"]]
