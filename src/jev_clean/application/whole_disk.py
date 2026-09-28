"""Entire declared filesystem scope, every regular file assessed before safety veto.

No default file/directory/time cap. Exact model-input cache reuse is reported separately.
"""

from __future__ import annotations

import hashlib
import os
import stat
import time
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from jev_clean.domain.models import Candidate, DiskNode, ExplorationResult, ExplorationStep, Fingerprint
from jev_clean.domain.policy import apply_policy, kind_for_path
from jev_clean.infrastructure.decision_cache import DecisionCache
from jev_clean.infrastructure.disk_walk import FileMeta, walk_privileged, walk_user
from jev_clean.infrastructure.model import state_for
from jev_clean.infrastructure.paths import aliases_covered_elsewhere, firmlinks, logical_path
from jev_clean.infrastructure.scanner import no_symlink_ancestors
from jev_clean.infrastructure.volumes import DiskScope, normalize_roots, startup_scope


def context_hint(path: Path, kind: str) -> str:
    if kind in ("user-cache", "package-cache", "rotated-log"):
        return kind
    suffix = path.suffix.lower()
    if suffix in {".db", ".sqlite", ".sqlite3", ".sql", ".wal"}:
        return "database"
    if suffix in {".safetensors", ".gguf", ".onnx", ".pt", ".pth"}:
        return "model weights"
    if suffix in {".py", ".js", ".ts", ".tsx", ".rs", ".go", ".c", ".cpp", ".h", ".swift", ".java", ".kt"}:
        return "source code"
    if suffix in {".pem", ".key", ".p12", ".pfx"} or path.name.startswith(".env"):
        return "credentials or configuration"
    if suffix in {".zip", ".gz", ".zst", ".tar", ".age", ".7z"}:
        return "archive or backup"
    if suffix in {".dmg", ".vmdk", ".qcow2", ".raw", ".iso"}:
        return "disk image"
    if suffix in {".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov", ".mp3", ".wav"}:
        return "personal media"
    return "unclassified file"


def candidate(path: Path, meta: FileMeta, home: Path, opened: set[str] | None, epoch: float) -> Candidate:
    exact = True
    try:
        current = FileMeta.from_stat(path.lstat())
        if (current.device, current.inode) != (meta.device, meta.inode):
            exact = False
        else:
            meta = current
    except OSError:
        exact = False
    fp = Fingerprint(meta.device, meta.inode, meta.size, meta.mtime_ns, meta.ctime_ns, meta.uid, meta.nlink)
    kind = kind_for_path(path, home) or "protected"
    if meta.uid != os.getuid():
        kind = "protected"
    identity = hashlib.sha256(f"{path}:{fp}".encode(errors="surrogatepass")).hexdigest()[:20]
    return Candidate(
        identity,
        str(path),
        kind,
        meta.blocks * 512,
        max(0, epoch - meta.mtime_ns / 1e9),
        fp,
        stat.S_ISREG(meta.mode),
        stat.S_ISLNK(meta.mode),
        exact,
        None if opened is None else str(path) in opened,
        context_hint=context_hint(path, kind),
    )


def bucket_for(path: Path, home: Path) -> str:
    """Disjoint display groups; direct files never masquerade as an ancestor subtree."""
    if path.is_relative_to(home):
        relative = path.relative_to(home).parts
        if len(relative) == 1:
            return str(home / "[files]")
        if relative[0] == "Library":
            return str(home / "Library" / (relative[1] if len(relative) > 2 else "[files]"))
        return str(home / relative[0])
    parts = path.parts
    if len(parts) <= 2:
        return "/[files]"
    if len(parts) == 3:
        return str(path.parent / "[files]")
    return str(Path(*parts[:3]))


def investigate_disk(
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
    scope = startup_scope() if roots is None else DiskScope(list(dict.fromkeys(roots)), kind="custom")
    for root in scope.roots:
        if not root.is_absolute() or ".." in root.parts or not no_symlink_ancestors(root):
            raise ValueError("Read scope must be absolute and non-symlink")
    scope.roots = normalize_roots(scope.roots)
    state_dir = state_dir or home / ".local/state/jev-clean/disk-scan"
    exclusions = [state_dir, Path("/System/Volumes/Data") / state_dir.relative_to("/")]
    mappings = firmlinks()
    result = ExplorationResult()
    stats: dict = {
        "scope": scope.kind,
        "observed_entries": 0,
        "observed_regular_files": 0,
        "model_assessed_files": 0,
        "model_assessed_protected_files": 0,
        "fresh_model_inferences": 0,
        "reused_model_decisions": 0,
        "directories_observed": 0,
        "symlinks_observed": 0,
        "special_entries_observed": 0,
        "approved": 0,
        "model_remove": 0,
        "model_kept": 0,
        "model_review": 0,
        "protected_files": 0,
        "permission_or_io_events": 0,
        "issue_events": 0,
        "filesystem_boundaries": 0,
        "scanner_state_exclusions": 0,
        "covered_aliases": 0,
        "walk_finished": False,
        "roots_total": len(scope.roots),
        "roots_finished": 0,
        "directory_model_decisions": 0,
        "open_file_check_available": open_paths is not None,
    }
    guards: Counter[str] = Counter()
    issues: list[dict] = []
    buckets: dict[str, int] = {}
    bad_paths: set[Path] = set()
    roots_coverage = []
    last_progress = time.monotonic()
    covered_aliases: list[Path] = []

    def issue(path, reason):
        if reason == "scanner-state exclusion" and any(
            Path(path) == p or Path(path).is_relative_to(p) for p in covered_aliases
        ):
            stats["covered_aliases"] += 1
            return
        stats["issue_events"] += 1
        if reason == "filesystem boundary":
            stats["filesystem_boundaries"] += 1
        elif reason == "scanner-state exclusion":
            stats["scanner_state_exclusions"] += 1
            bad_paths.add(logical_path(Path(path), mappings))
        else:
            stats["permission_or_io_events"] += 1
            bad_paths.add(logical_path(Path(path), mappings))
        if len(issues) < 100:
            issues.append({"path": path, "reason": reason})

    with DecisionCache(state_dir, advisor, scope.roots, mode) as cache:
        # Disk-backed identity tracking avoids holding millions of inode tuples in RAM.
        cache.db.execute(
            "CREATE TABLE IF NOT EXISTS seen_dirs (dev INTEGER, ino INTEGER, PRIMARY KEY(dev,ino)) WITHOUT ROWID"
        )
        cache.db.execute(
            "CREATE TABLE IF NOT EXISTS seen_links (dev INTEGER, ino INTEGER, PRIMARY KEY(dev,ino)) WITHOUT ROWID"
        )
        cache.db.execute("DELETE FROM seen_dirs")
        cache.db.execute("DELETE FROM seen_links")

        def directory(meta):
            return (
                cache.db.execute(
                    "INSERT OR IGNORE INTO seen_dirs VALUES (?,?)", (meta.device, meta.inode)
                ).rowcount
                == 1
            )

        stats["resumed_decision_cache"] = cache.resumed
        stats["inventory_started_at"] = datetime.now(timezone.utc).isoformat()
        stats["assessment_epoch"] = datetime.fromtimestamp(cache.epoch, timezone.utc).isoformat()
        progress("Whole startup disk" if roots is None else "Custom full scope")
        progress("All regular files reach model assessment; no sample or duration cap.")
        if cache.resumed:
            progress("Restart: filesystem rechecked, exact model decisions reused.")
        pending = list(scope.roots)
        while pending and not cancelled():
            options = [DiskNode(str(p), None, True, 0, False) for p in pending[:6]]
            choice = advisor.choose_directory(options, mode)
            index = int(choice.choice.removeprefix("n"))
            if not 0 <= index < len(options):
                raise ValueError("Model selected an unavailable volume")
            root = pending.pop(index)
            result.steps.append(ExplorationStep(str(root), choice, 0))
            before = stats["permission_or_io_events"]
            before_files = stats["observed_regular_files"]
            progress("Laya chose volume " + str(root))
            walker = walk_privileged if deep else walk_user
            covered_aliases = aliases_covered_elsewhere(root, scope.roots, mappings)
            for entry in walker(
                root,
                exclusions=exclusions + covered_aliases,
                issue=issue,
                directory=directory,
                cancelled=cancelled,
            ):
                if cancelled():
                    break
                stats["observed_entries"] += 1
                meta = entry.metadata
                path = logical_path(entry.path, mappings)
                if stat.S_ISDIR(meta.mode):
                    stats["directories_observed"] += 1
                    continue
                if stat.S_ISLNK(meta.mode):
                    stats["symlinks_observed"] += 1
                    continue
                if not stat.S_ISREG(meta.mode):
                    stats["special_entries_observed"] += 1
                    continue
                stats["observed_regular_files"] += 1
                allocated = meta.blocks * 512
                if (
                    meta.nlink > 1
                    and cache.db.execute(
                        "INSERT OR IGNORE INTO seen_links VALUES (?,?)", (meta.device, meta.inode)
                    ).rowcount
                    == 0
                ):
                    allocated = 0
                bucket = bucket_for(path, home)
                buckets[bucket] = buckets.get(bucket, 0) + allocated
                item = candidate(path, meta, home, open_paths, cache.epoch)
                state = state_for(item)
                decision = cache.get(state)
                if decision is None:
                    decision = advisor.predict(item)
                    cache.put(state, decision)
                    stats["fresh_model_inferences"] += 1
                else:
                    decision = replace(decision, reused=True, elapsed_ms=0.0)
                    stats["reused_model_decisions"] += 1
                stats["model_assessed_files"] += 1
                # Explicit invariant: no eligibility test before model assessment.
                reviewed = apply_policy(item, decision)
                stats["model_" + ("kept" if decision.choice == "keep" else decision.choice)] += 1
                if not reviewed.eligible:
                    stats["protected_files"] += 1
                    stats["model_assessed_protected_files"] += 1
                    guards[reviewed.reason] += 1
                if mode == "clean" and reviewed.selectable:
                    result.candidates.append(reviewed)
                    stats["approved"] += 1
                if time.monotonic() - last_progress >= 1:
                    progress(
                        f"{stats['observed_regular_files']:,} files scanned · {stats['model_assessed_files']:,} model-assessed "
                        f"({stats['fresh_model_inferences']:,} new / {stats['reused_model_decisions']:,} reused) · {stats['approved']:,} approved"
                    )
                    cache.save_progress(stats, False)
                    last_progress = time.monotonic()
            result.steps[-1].children_seen = stats["observed_regular_files"] - before_files
            finished = not cancelled()
            roots_coverage.append(
                {
                    "path": str(root),
                    "finished": finished,
                    "issue_events": stats["permission_or_io_events"] - before,
                }
            )
            if finished:
                stats["roots_finished"] += 1
        stats["walk_finished"] = not cancelled() and stats["roots_finished"] == len(scope.roots)
        for group_path, size in sorted(buckets.items(), key=lambda pair: pair[1], reverse=True):
            p = Path(group_path)
            complete = bool(
                stats["walk_finished"]
                and not any(b == p or b.is_relative_to(p) or p.is_relative_to(b) for b in bad_paths)
            )
            node = DiskNode(group_path, size, not group_path.endswith("/[files]"), 0, complete)
            if mode == "status" and not cancelled():
                node.purpose = advisor.classify(node)
                stats["directory_model_decisions"] += 1
                progress(f"Laya: {group_path} → {node.purpose.choice}")
            result.nodes.append(node)
        result.complete = bool(
            stats["walk_finished"]
            and not cancelled()
            and not stats["permission_or_io_events"]
            and not stats["scanner_state_exclusions"]
            and not scope.exclusions
        )
        stats["model_assessed"] = stats["model_assessed_files"]
        stats["observed_files"] = stats["observed_regular_files"]
        stats["guard_reasons"] = dict(guards)
        stats["coverage"] = {
            "roots": roots_coverage,
            "requested_roots": list(map(str, scope.roots)),
            "scope": scope.kind,
            "exclusions": scope.exclusions,
            "issues": issues,
            "issue_details_truncated": stats["issue_events"] > len(issues),
            "scope_finished": stats["walk_finished"],
            "complete": result.complete,
            "symlinks": "observed, never followed; not regular-file model decisions",
            "external_mounts": "not traversed unless explicit roots",
            "state_cache": "scanner-owned growing journal is explicitly excluded",
            "model_reuse": "Every observed regular file assessed. Exact identical model inputs reuse prior neural output; fresh/reused counts are separate.",
            "resume": "Re-enumerate filesystem on restart; reuse exact model decisions, not stale file identities. Counters describe this pass.",
        }
        cache.save_progress(stats, bool(stats["walk_finished"] and not cancelled()))
    if not result.complete:
        result.warnings.append(
            "Not complete: cancelled, permission gaps or declared scope exclusions. See coverage."
        )
    result.stats = stats
    return result
