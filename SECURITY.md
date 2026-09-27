# Safety and security

This is an **alpha cleanup reviewer**, not a guarantee that deletion is harmless. Start with `--demo`, then inspect a JSON plan. Close relevant applications before moving files. Keep backups.

## Permission boundary

The entire app refuses root. The TUI offers sudo diagnostics on each of Clean and Status. Authentication is `/usr/bin/sudo -v` attached to the real terminal, with no password captured. Elevated subprocesses are fixed native read-only commands. Canceling or failing authentication does not start the operation. The user can explicitly choose unprivileged inspection; the mandatory model still runs and coverage gaps remain visible. Sudo does not bypass SIP, TCC or Full Disk Access. No system helper/daemon is installed and no sudoers/PAM configuration is modified.

## Deletion boundary

No permanent deletion or recursive directory cleanup. Reviewable **files only** come from `ROOTS` in `domain/policy.py`: stale user/package caches and rotated logs. Model results cannot expand these roots or authorize protected files. Recent files, symlinks, hard links, another UID, special files, credential/database/source/model/VM-like suffixes and active/unknown-open files are rejected. Each inspected directory stays on its own filesystem and does not follow symlinks. Exploration is bounded; unvisited data stays unknown. Incomplete file metadata or a partial directory listing prevents authorization for affected candidates. Cancelled investigations cannot authorize cleanup.

Plans expire in one hour. Applying a plan checks HOME, schema, completeness, selected IDs, and confirmation. The executor independently recalculates policy and revalidates device/inode/size/mtime/ctime/UID/link count, using no-follow directory descriptors. A private transaction lock serializes jev-clean operations. Each file is journaled before moving into a uniquely named batch under `~/.Trash`. Undo uses a no-overwrite link/unlink sequence and checks staged identity. A crash can leave a pending record; history keeps it visible and restore checks whether its file reached Trash.

### What is not proven

File age and placement do not prove disposability. Some apps misuse cache roots; inspect unfamiliar entries. `lsof` is a point-in-time check and can miss privileged processes without visibility. A same-user concurrent filesystem adversary can race inspection and rename; this is not a sandbox against another process with your permissions. Stop other writers and re-scan. Root-owned cleanup is intentionally unsupported. Finder/APFS may not immediately report reclaimed bytes; **moving to Trash frees no space**. APFS sparse/clone/hard-link/shared blocks mean allocated size is not a promise of exclusive reclaim. Backups/snapshots can retain deleted blocks.

## AI and privacy

Removal decisions use bounded engine-derived metadata: type, age, size and filesystem facts. Exploration/classification additionally uses bounded local folder-label hints, treated as untrusted data. No file contents or remote uploads. The model is mandatory for both modes, and applying a plan re-assesses selection with it. Missing/failed inference stops the operation; there is no rules-only fallback. The official installer automatically provisions weights pinned by HF revision, verifies their manifest and SHA256 checksums, and runs real inference before reporting ready. Direct-package installs automatically provision a missing cache on first use. This can download ~0.85 GB; download or integrity failure stops installation/operation without fallback. Published model confidence is **not calibrated deletion-safety confidence** for this domain. Model choice and options are strictly validated; unknown/NaN/malformed results cannot become a recommendation. We make no “zero hallucinations means safe cleanup” claim.

Reports and journals are mode 0600 in private user-owned storage. JSON exports may contain sensitive paths: keep them private. Public screenshots contain synthetic paths with real model inference; hermetic tests use explicit neural-adapter doubles, unavailable as an app flag. No telemetry. Update checks contact the project's fixed GitHub releases API; applying an update needs a separate interactive confirmation and never pipes fetched text into a shell.

## Reporting

Do not include private file lists or credentials in public issues. Use GitHub private vulnerability reporting if enabled, or send a minimal synthetic reproducer via the maintainer contact on GitHub. Until triaged, do not use a proposed bypass to remove user data.
