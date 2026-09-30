# Safety and security

**The model decides; the code only executes.** The local model supplies
keep/review/remove; no file-type rule can veto that judgment. The executor still
requires an unchanged target identity, current-user regular files, human selection
and final confirmation. The bundled Laya model is **not** guaranteed accurate: a
published 24-scenario diagnostic (ADR 0005) includes two incorrect-remove answers
(unique private key, required offline model weights). **Review every proposed
file.** Nothing here guarantees deletion is harmless. Start with `--demo`, then
inspect a JSON plan. Keep backups.

## Permission boundary

The entire app refuses root. Clean offers a Yes/No sudo question. Authentication
uses `/usr/bin/sudo -v` attached to the real terminal; Python never captures a
password. Elevated subprocesses are fixed native read-only diagnostics, including
NUL-delimited find and ordinal-only stat reads. No model-generated command, root
Python/model process, privileged cleanup, helper daemon, sudoers/PAM modification
or SIP/TCC bypass is provided. Permission gaps are reported, not treated as zero.

## Judgment versus execution

Only the mandatory model decides keep/review/remove. There are no application
trash rules based on directory allowlists, extensions, age thresholds, open
handles or hard-link count. Those observations are evidence, not permission to
remove. Unknown references or regenerability remain unknown. A remove judgment
is recorded even if the executor cannot carry it out; a mechanical refusal does
not rewrite the judgment. Valid keep/review answers are never selectable.

Execution supports current-user-owned regular files only, with human-selected
IDs and final confirmation. No recursive deletion or automatic Trash emptying.
No-follow directory descriptors, canonical paths, unchanged device/inode/size/
mtime/ctime/UID/link-count fingerprints, operation permissions and a private
transaction lock protect execution integrity. The executor cannot relocate its
own state or already staged files. Cross-device rename fails rather than copying
and deleting. Symlink/special-file staging is unsupported, not a trash label.

Plans expire in one hour and bind HOME/schema/candidate completeness. Applying a
plan collects fresh metadata, activity and manifest observations and reruns the
model. Changed target identity requires another scan and user review. Activity
changing again at execution requires reassessment; unknown activity alone is not
a classification veto. Cancellation does not leave an actionable scan. Partial
whole-disk coverage is reported separately from exact individual target metadata.

Files are journaled before moving to a unique batch under `~/.Trash`. Undo checks
staged identity and uses no-overwrite link/unlink. A crash can leave a pending
record; history and restore keep recovery possible. **Trash staging frees no
space.** APFS sparse/shared/clone/hard-link allocation and snapshots prevent byte
counts from promising exclusive physical reclaim.

## AI and privacy

Local inputs contain bounded directory labels, extension, measured filesystem
facts and installed app ID/version observations. Resource contents, basenames and
absolute home paths are omitted. Only bounded installed-application Info.plist
metadata is read for app matching. ID equality is not ownership/dependency proof.
All external labels are data, not instructions; prompt injection and semantic
misclassification remain model risks. Non-English labels are not reliably
understood by this English checkpoint. Oversized inputs explicitly fail instead
of silently dropping evidence. No remote inference, telemetry or report uploads.

The installer provisions pinned weights, checks manifest/SHA256 integrity and
runs real inference before Ready. A direct install self-provisions missing weights.
Readiness means the runtime works, **not that cleanup judgments are correct**.
No model-free fallback. Confidence is not calibrated deletion-safety probability.
Typed choices/distributions are validated; malformed output is not a recommendation.
This local Laya backend is not official TypeSafe Jev.

Reports/journals are private mode 0600. Decision caches reject symlink/hard-link/
foreign-owned state, lock concurrent scans and key reuse by exact input, question,
label mapping, input contract and pinned model/runtime. Fresh and reused decisions
are separate counters. Scanner state is excluded from its own inventory. Reports
contain private paths; never upload them. Demos use synthetic metadata with real
inference; test doubles exist only at explicit external neural boundaries.

## Limits and reporting

Same-user concurrent processes can race observation and rename; this is not a
sandbox against an adversary with the same permissions. Close writers and retain
backups. Age, size, a cache-like name, an absent open handle or a stopped VM do not
establish disposability. App-native dependency probes, resource grouping and validated cleanup accuracy
remain unfinished. The owner authorized this alpha release with those limitations;
that authorization does not establish safe judgments for other users.

Report vulnerabilities with a minimal synthetic reproducer via GitHub private
vulnerability reporting if enabled, or the maintainer contact. Never publish
private file lists or credentials, and never test a bypass by removing user data.
Update checks use the fixed GitHub releases endpoint; applying an update requires
separate interactive confirmation and never pipes downloaded text to a shell.
