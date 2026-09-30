"""Local factual context; no disposal labels or application-specific cleanup rules.

Only bounded installed-application manifests are read. Resource file contents and
filenames never enter inference. Directory labels are untrusted local data.
"""

from __future__ import annotations

import os
import plistlib
import stat
from pathlib import Path


class EvidenceCollector:
    def __init__(self, home: Path):
        self.home = home
        self.applications: dict[str, set[str]] | None = None

    def _applications(self) -> dict[str, set[str]]:
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
        facts = {
            "location": "/".join(p[:40] for p in parts[-4:]) or "[home]",
            "extension": path.suffix[:20] or "[none]",
            "application": "unknown",
            "application_version": "unknown",
            "application_match": "unknown",
            "references": "unknown",
            "regenerability": "unknown",
        }
        # An identifier equality is evidence of a naming relationship, NOT ownership
        # proof, current use, obsolescence, or proof that another version is removable.
        matches = [(part, self._applications()[part]) for part in parts if part in self._applications()]
        if len(matches) == 1:
            identifier, versions = matches[0]
            facts.update(
                application=identifier[:80],
                application_version=",".join(sorted(versions))[:80],
                application_match="directory identifier match; ownership not proven",
            )
        return facts
