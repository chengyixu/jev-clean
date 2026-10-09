"""Fast native resource inventory. Location layout is discovery, never a disposal rule."""

from __future__ import annotations

import os
import stat
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

from jev_clean.domain.models import Candidate
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.native import _stream_du
from jev_clean.infrastructure.paths import aliases_covered_elsewhere, firmlinks, logical_path
from jev_clean.infrastructure.resource_tree import directory_fd
from jev_clean.infrastructure.scanner import candidate_from_stat, fingerprint, no_symlink_ancestors
from jev_clean.infrastructure.volumes import DiskScope, normalize_roots


@dataclass
class Frontier:
    paths: list[Path] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    symlinks: int = 0
    aliases: int = 0


def split_locations(home: Path) -> set[Path]:
    """Organizational containers to open, not directories approved for removal.

    Every sibling remains represented. Opaque trees are measured as a resource;
    this set changes granularity only, never scope or disposition.
    """
    relative = (
        "Library",
        "Library/Caches",
        "Library/Logs",
        "Library/Application Support",
        "Library/Developer",
        "Library/Developer/Xcode",
        "Library/Developer/Xcode/DerivedData",
        "Library/Developer/Xcode/iOS DeviceSupport",
        "Library/Developer/CoreSimulator",
        ".cache",
        ".npm",
        ".gradle",
        "Downloads",
        "Library/pnpm",
    )
    return {
        home,
        *home.parents,
        *(home / p for p in relative),
        Path("/Library"),
        Path("/System"),
        Path("/System/Volumes"),
        Path("/private"),
        Path("/private/var"),
        Path("/opt"),
        Path("/usr"),
    }


def discover_resources(home: Path, scope: DiskScope, cancelled=lambda: False) -> Frontier:
    result = Frontier()
    roots = normalize_roots(scope.roots)
    mappings = firmlinks()
    split = split_locations(home)
    seen: set[tuple[int, int]] = set()
    own_state = home / ".local/state/jev-clean"

    def issue(p: Path, reason: str):
        result.issues.append({"path": str(p), "reason": reason})

    for root in roots:
        if cancelled():
            break
        if not root.is_absolute() or ".." in root.parts or not no_symlink_ancestors(root):
            raise ValueError("Read scope must be absolute and non-symlink")
        aliases = aliases_covered_elsewhere(root, roots, mappings)
        try:
            device = root.stat().st_dev
        except OSError:
            issue(root, "root metadata unavailable")
            continue
        pending = [(root, True)]
        while pending and not cancelled():
            p, force_split = pending.pop()
            if any(p == a or p.is_relative_to(a) for a in aliases):
                result.aliases += 1
                continue
            try:
                st = p.lstat()
                if stat.S_ISLNK(st.st_mode):
                    result.symlinks += 1
                    continue
                if st.st_dev != device:
                    issue(p, "filesystem boundary; separately requested roots scanned independently")
                    continue
                logical = logical_path(p, mappings)
                if logical == own_state or logical.is_relative_to(own_state):
                    issue(logical, "scanner-state exclusion")
                    continue
                if stat.S_ISDIR(st.st_mode):
                    identity = (st.st_dev, st.st_ino)
                    if identity in seen:
                        result.aliases += 1
                        continue
                    seen.add(identity)
                    # Also split ancestors of excluded aliases/state and other requested
                    # mounts so native du cannot silently re-traverse those subtrees.
                    structural = any(a != p and a.is_relative_to(p) for a in aliases)
                    structural |= own_state != logical and own_state.is_relative_to(logical)
                    structural |= any(r != p and r.is_relative_to(p) for r in roots)
                    if force_split or logical in split or structural:
                        with directory_fd(p) as fd:
                            held = os.fstat(fd)
                            if (held.st_dev, held.st_ino) != identity:
                                issue(p, "directory identity changed before enumeration")
                                continue
                            with os.scandir(fd) as entries:
                                children = [p / e.name for e in entries]
                        if children:
                            pending.extend((c, False) for c in sorted(children, reverse=True))
                            continue
                    # An empty directory is also an observed resource.
                    result.paths.append(logical)
                elif stat.S_ISREG(st.st_mode):
                    result.paths.append(logical)
                else:
                    issue(logical, "special entry; unsupported resource")
            except OSError:
                issue(p, "directory enumeration or metadata unavailable")
    # Aliases may have produced the same logical label. Never count it twice.
    result.paths = list(dict.fromkeys(result.paths))
    return result


def measure_resource(
    path: Path,
    home: Path,
    evidence: EvidenceCollector,
    opened: set[str] | None,
    *,
    deep: bool = False,
    cancelled=lambda: False,
    timeout: float = 30,
) -> Candidate:
    if not no_symlink_ancestors(path):
        raise ValueError("Symlink resource refused")
    before = path.lstat()
    item = candidate_from_stat(path, before, home, opened, evidence)
    if stat.S_ISREG(before.st_mode):
        return item
    if not stat.S_ISDIR(before.st_mode):
        raise ValueError("Unsupported resource type")
    # du reads descendants natively without returning millions of Python objects.
    # A timeout is an explicit measurement gap, not zero or a completed subtree.
    command = ["/usr/bin/du", "-x", "-k", "-s", str(path)]
    if deep:
        command = ["/usr/bin/sudo", "-n", *command]
    code, out, err = _stream_du(command, timeout, cancelled, lambda _: None)
    amount, sep, label = out.partition("\t")
    valid = bool(sep and amount.strip().isdigit() and label == str(path) + "\n")
    size = int(amount) * 1024 if valid else 0
    after = path.lstat()
    unchanged = fingerprint(before) == fingerprint(after)
    complete = code == 0 and not err.strip() and valid and unchanged and not cancelled()
    facts = dict(item.evidence)
    facts["location"] = evidence.collect(path / "[resource]")["location"]
    facts["measurement"] = "native allocated subtree total; descendants not individually model-assessed"
    facts["membership"] = "exact descendant manifest captured only for selected review"
    active = None if opened is None else any(p == str(path) or p.startswith(str(path) + "/") for p in opened)
    return replace(
        item,
        unit="directory",
        regular=False,
        allocated_bytes=size,
        scan_complete=complete,
        open_file=active,
        evidence=facts,
        eligible=False,
        reason="Awaiting mandatory resource model judgment",
        execution_issue=(
            "Current-user staging cannot act for another owner"
            if before.st_uid != os.getuid()
            else "Native resource measurement incomplete"
            if not complete
            else ""
        ),
        age_seconds=max(0, time.time() - before.st_mtime),
    )
