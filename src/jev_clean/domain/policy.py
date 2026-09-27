"""Single source of truth. A model can never turn a veto into permission."""

from dataclasses import replace
from pathlib import Path

from jev_clean.domain.models import Candidate, Decision

# File-level cleanup only. Never broaden these to whole Application Support,
# .local, developer source roots, VM images, databases, or arbitrary directories.
ROOTS = (
    ("Library/Caches", "user-cache", 30),
    (".cache/pip", "package-cache", 30),
    ("Library/Logs", "rotated-log", 14),
    ("Library/Application Support/com.netease.uuremote/Logs", "rotated-log", 14),
)
FORBIDDEN_SUFFIXES = {
    ".yaml",
    ".yml",
    ".toml",
    ".env",
    ".token",
    ".credentials",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".kt",
    ".java",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".sql",
    ".wal",
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".kdbx",
    ".safetensors",
    ".gguf",
    ".qcow2",
    ".raw",
    ".dmg",
    ".age",
    ".py",
    ".js",
    ".ts",
    ".swift",
    ".go",
    ".rs",
    ".sh",
    ".json",
    ".plist",
}
FORBIDDEN_PARTS = {
    ".git",
    ".ssh",
    "keychains",
    "credentials",
    "auth.json",
    "cookies",
    "local storage",
    "indexeddb",
    "session storage",
    "login data",
    "history",
    "sessions",
    "postgresql",
    "models",
    "backups",
}


def kind_for_path(path: Path, home: Path) -> str | None:
    try:
        relative = path.relative_to(home)
    except ValueError:
        return None
    if path.name.lower().startswith(".env"):
        return None
    if any(part.lower() in FORBIDDEN_PARTS for part in relative.parts):
        return None
    if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name.lower().endswith(("-wal", "-shm")):
        return None
    for root, kind, _ in ROOTS:
        base = Path(root)
        if relative != base and relative.is_relative_to(base):
            if kind == "rotated-log":
                name = path.name.lower()
                # Deliberately exclude active .log and extensionless logs.
                if not (name.endswith((".log.gz", ".log.old")) or ".log." in name):
                    return None
            return kind
    return None


def apply_policy(item: Candidate, decision: Decision | None = None) -> Candidate:
    reason = ""
    if not item.regular or item.symlink:
        reason = "Not a regular non-symlink file"
    elif item.fingerprint.nlink != 1:
        reason = "Hard-linked file; shared ownership of contents"
    elif not item.scan_complete:
        reason = "Partial scan; review after a complete scan"
    elif item.kind not in {r[1] for r in ROOTS}:
        reason = "Protected or unrecognized data; never a cleanup target"
    elif item.open_file is None:
        reason = "Open-file check unavailable; fail closed"
    elif item.open_file:
        reason = "File is in use by a process"
    elif item.age_seconds < (14 if item.kind == "rotated-log" else 30) * 86400:
        reason = "Too recent; within the retention window"
    eligible = not reason
    if eligible:
        reason = "Old, unopened file in an allowlisted disposable root; user review required"
    recommended = bool(
        eligible
        and decision
        and decision.choice == "remove"
        and decision.probabilities.get("remove", 0) > 0
        and decision.probabilities.get("remove", 0) >= max(decision.probabilities.values(), default=1)
    )
    return replace(item, eligible=eligible, reason=reason, decision=decision, recommended=recommended)
