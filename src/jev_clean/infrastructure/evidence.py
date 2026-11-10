"""Local factual context; no disposal labels or application-specific cleanup rules.

Only bounded installed-application manifests are read. Resource file contents and
filenames never enter inference. Directory labels are untrusted local data.
"""

from __future__ import annotations

import os
import plistlib
import stat
from collections import Counter
from pathlib import Path

from jev_clean.infrastructure.paths import directory_fd

CACHE_NAMESPACE_CONTRACT = "Apple documents the macOS Library/Caches namespace for app-specific support data that the app can re-create easily. Apps can misuse a namespace; this does not prove the contents are unwanted or contain no unique data."
LOG_NAMESPACE_CONTRACT = "The macOS Library/Logs namespace stores application diagnostic logs. A current writer, support-case need and retention obligation require observation; log placement alone does not prove disposal."

# The single home of every verified storage role: (namespace label, documented purpose).
# A purpose describes what the owner keeps there, never a permission to remove it.
STORAGE_ROLES: dict[str, tuple[str, str]] = {
    "macos-cache": ("macOS Library/Caches", CACHE_NAMESPACE_CONTRACT),
    "macos-diagnostic-log": ("macOS Library/Logs", LOG_NAMESPACE_CONTRACT),
    "xcode-derived-data": (
        "Xcode DerivedData",
        "Xcode keeps per-project build products, indexes and build logs here and re-creates them when the project is built again. An open project or a running build can be using them.",
    ),
    "xcode-device-support": (
        "Xcode DeviceSupport",
        "Xcode copies debug symbols for a connected device's OS version here and copies them again the next time a device with that OS version is used for debugging.",
    ),
    "xcode-archives": (
        "Xcode Archives",
        "Xcode keeps app archives here, including the debug symbols needed to read crash reports from distributed builds. Building again cannot re-create a past archive.",
    ),
    "simulator-devices": (
        "Xcode Simulator devices",
        "Simulator devices with their installed apps and app data. The owner tool, xcrun simctl, manages devices; app data inside a device can be unique.",
    ),
    "ios-device-backup": (
        "Finder iPhone and iPad backups",
        "Finder keeps local iPhone and iPad backups here. A backup can hold the only copy of device data such as messages and photos; whether another copy exists is not observed.",
    ),
    "user-downloads": (
        "user Downloads folder",
        "The user's Downloads folder holds files the user downloaded or saved. Whether a file is still needed or exists elsewhere is not observed.",
    ),
    "mail-store": (
        "Apple Mail data",
        "Apple Mail keeps local mailboxes, messages and attachments here. Messages of accounts without a server copy exist only here.",
    ),
    "messages-store": (
        "Apple Messages data",
        "Apple Messages keeps the local conversation history and attachments here. Without Messages in iCloud this can be the only copy.",
    ),
    "icloud-drive": (
        "iCloud Drive",
        "iCloud Drive and app documents synced with iCloud. Removing a synced file removes it from iCloud and from every device that syncs it.",
    ),
    "credential-store": (
        "SSH or GnuPG key store",
        "Secure shell and GnuPG keys and configuration. A private key here can be the only copy and can grant access to other systems.",
    ),
}
UNVERIFIED_CONTRACT = "No source establishes this resource's storage purpose."

# Exact roots below HOME, most specific first. No substring or leaf-label guessing.
_HOME_ROOTS: tuple[tuple[str, str], ...] = (
    ("Library/Caches", "macos-cache"),
    ("Library/Logs", "macos-diagnostic-log"),
    ("Library/Developer/Xcode/DerivedData", "xcode-derived-data"),
    *(
        (f"Library/Developer/Xcode/{system} DeviceSupport", "xcode-device-support")
        for system in ("iOS", "iPadOS", "watchOS", "tvOS", "visionOS", "macOS")
    ),
    ("Library/Developer/Xcode/Archives", "xcode-archives"),
    ("Library/Developer/CoreSimulator/Devices", "simulator-devices"),
    ("Library/Application Support/MobileSync/Backup", "ios-device-backup"),
    ("Downloads", "user-downloads"),
    ("Library/Mail", "mail-store"),
    ("Library/Messages", "messages-store"),
    ("Library/Mobile Documents", "icloud-drive"),
    (".ssh", "credential-store"),
    (".gnupg", "credential-store"),
)


def name_token(name: str) -> str:
    """Lower-case suffix token; a leading-dot name without another dot (.git, .ssh) is its own token."""
    lower = name.lower()
    suffix = Path(lower).suffix or (lower if lower.startswith(".") and len(lower) > 1 else "")
    return suffix[:24] or "[none]"


def observe_storage_role(path: Path, home: Path) -> dict[str, str]:
    """Exact verified OS storage namespace; never a model choice or permission.

    Canonical roots only, no substring/leaf-label guessing. The contract describes
    what the namespace is for, not a guarantee that every file obeys that purpose.
    """
    if any(p.is_symlink() for p in (path, *path.parents)):
        return {"storage_namespace": "unverified", "namespace_contract": UNVERIFIED_CONTRACT}
    roots = [(Path("/Library/Caches"), "macos-cache"), (Path("/Library/Logs"), "macos-diagnostic-log")]
    roots += [(home / relative, role) for relative, role in _HOME_ROOTS]
    try:
        parts = path.relative_to(home).parts
    except ValueError:
        parts = ()
    if (
        len(parts) >= 6
        and parts[:2] == ("Library", "Containers")
        and parts[3:6] == ("Data", "Library", "Caches")
    ):
        roots.append((home.joinpath(*parts[:6]), "macos-cache"))
    if (
        len(parts) >= 5
        and parts[:2] == ("Library", "Group Containers")
        and parts[3:5] == ("Library", "Caches")
    ):
        roots.append((home.joinpath(*parts[:5]), "macos-cache"))
    for root, role in roots:
        if path.is_relative_to(root):
            return {"storage_namespace": role, "namespace_contract": STORAGE_ROLES[role][1]}
    return {"storage_namespace": "unverified", "namespace_contract": UNVERIFIED_CONTRACT}


def _most_common(counts: Counter[str], limit: int = 8) -> str:
    """Highest counts first, equal counts by name: the input never depends on directory order."""
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]
    return ", ".join(f"{k}:{v}" for k, v in ranked)


def observe_children(path: Path, *, limit: int = 64) -> dict[str, str]:
    """Bounded immediate-entry structural observations, not a content classifier.

    No basenames/content enter inference; suffix counts are untrusted observations.
    A sample is never interpreted as proof of subtree purity or regenerability.
    """
    if not 1 <= limit <= 256:
        raise ValueError("Immediate-entry observation limit must be 1–256")
    files: Counter[str] = Counter()
    directories: Counter[str] = Counter()
    types: Counter[str] = Counter()
    count, complete = 0, True
    with directory_fd(path) as fd:
        with os.scandir(fd) as entries:
            for entry in entries:
                if count >= limit:
                    complete = False
                    break
                info = entry.stat(follow_symlinks=False)
                suffix = name_token(entry.name)
                if stat.S_ISREG(info.st_mode):
                    files[suffix] += 1
                    types["regular"] += 1
                elif stat.S_ISDIR(info.st_mode):
                    directories[suffix] += 1
                    types["directory"] += 1
                elif stat.S_ISLNK(info.st_mode):
                    types["symlink"] += 1
                else:
                    types["special"] += 1
                count += 1
    return {
        "sampled_entries": str(count),
        "entry_types": ", ".join(f"{k}:{v}" for k, v in sorted(types.items())),
        "file_extensions": _most_common(files),
        "directory_extensions": _most_common(directories),
        "observation_scope": "all immediate entries; descendants uninspected"
        if complete
        else "partial immediate-entry sample; no subtree purity claim",
        "unique_data_status": "not established by metadata",
        "runtime_references": "not established by entry inspection",
    }


class EvidenceCollector:
    def __init__(self, home: Path):
        self.home = home
        self.applications: dict[str, set[str]] | None = None

    def application_metadata(self) -> dict[str, set[str]]:
        if self.applications is not None:
            return self.applications
        self.applications = {}
        for root in (Path("/Applications"), self.home / "Applications"):
            if any(p.is_symlink() for p in (root, *root.parents)):
                continue
            try:
                bundles = list(root.glob("*.app"))
            except OSError:
                continue
            for bundle in bundles:
                path = bundle / "Contents/Info.plist"
                if any(p.is_symlink() for p in (path, *path.parents)):
                    continue
                try:
                    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                    with os.fdopen(fd, "rb") as source:
                        metadata = os.fstat(source.fileno())
                        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > 256 * 1024:
                            continue
                        info = plistlib.loads(source.read(256 * 1024 + 1))
                    identifier = info.get("CFBundleIdentifier")
                    version = info.get("CFBundleShortVersionString", info.get("CFBundleVersion", "unknown"))
                    if isinstance(identifier, str) and isinstance(version, str):
                        self.applications.setdefault(identifier, set()).add(version[:40])
                except (OSError, ValueError, TypeError, AttributeError, OverflowError):
                    continue
        return self.applications

    def collect(self, path: Path) -> dict[str, str]:
        try:
            parent = path.parent.relative_to(self.home)
            parts = parent.parts
        except ValueError:
            # Do not include the login name of another account in the local prompt.
            parts = path.parent.parts[1:]
            if len(parts) > 1 and parts[0] == "Users":
                parts = ("Users", "[account]", *parts[2:])
        # Keep enclosing storage context as well as leaf directories. Taking
        # only the tail makes deep caches and project work indistinguishable.
        shown = parts if len(parts) <= 4 else (*parts[:2], "…", *parts[-2:])
        facts = {
            **observe_storage_role(path, self.home),
            "location": "/".join(p[:40] for p in shown) or "[home]",
            "extension": name_token(path.name),
            "application": "unknown",
            "application_version": "unknown",
            "application_match": "unknown",
            "references": "unknown",
            "regenerability": "unknown",
        }
        # An identifier equality is evidence of a naming relationship, NOT ownership
        # proof, current use, obsolescence, or proof that another version is removable.
        matches = [
            (part, self.application_metadata()[part]) for part in parts if part in self.application_metadata()
        ]
        if len(matches) == 1:
            identifier, versions = matches[0]
            facts.update(
                application=identifier[:80],
                application_version=",".join(sorted(versions))[:80],
                application_match="directory identifier match; ownership not proven",
            )
        return facts
