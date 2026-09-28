# Whole-disk scope and honest model coverage

## What changed in 0.2.0

The old default was a cache-oriented sample: a few user directories, per-directory observation limits, and a small model-assessment budget. That did **not** meet the whole-disk requirement. Those application paths are removed.

Both Clean and Status now discover the startup APFS container and walk the mounted filesystem scope, including system/data/VM/preboot/recovery/update roots where mounted. The booted system snapshot represents its underlying System volume once. Apple firmlink aliases are pruned only when their physical Data scope is explicitly covered; directory identities and hardlink allocation are tracked to avoid duplicate traversal/accounting.

The default has **no file-count, directory-count or scan-duration cutoff**. The model chooses volume order, but cannot silently omit the rest. Every observed **regular file**, including zero-byte, protected, source, database, model and credential files, receives a model decision before deletion safeguards are applied. No file contents are read. Path-derived type hints are metadata; arbitrary filenames and contents do not enter file-disposition inference.

Scanning everything does not mean deleting everything. The existing narrow mutation policy remains a veto after inference. User confirmation and execution-time identity/open-file checks remain mandatory.

## Scope is explicit

- Default: mounted startup-container filesystem scope, not only HOME/caches.
- `--root /path`: an explicitly labeled custom scope; it is never called a whole-disk scan. External disks can be inspected this way.
- No automatic mounting, unlocking, SIP/TCC bypass, remote-drive traversal or snapshot enumeration. Unmounted/locked startup volumes and filesystem boundaries are reported.
- Symlinks and special entries are counted but not followed or passed off as regular-file model assessments.
- The scanner's own growing journal is explicitly excluded to avoid self-inventory feedback.
- Permission and I/O gaps are recorded. “Walk finished” means traversal ended; it does **not** imply every protected path was accessible or that coverage was complete.

Sudo uses fixed native `find`/`stat` read operations. The app, model and cleanup executor never run as root. Paths are NUL-delimited and native stat results use numeric ordinals, not parseable filenames. Original identities are rechecked before any user-approved mutation.

## Scalable inference, not fabricated counts

A private SQLite cache is keyed by **exact serialized model input + question schema + pinned checkpoint + runtime identity**. Two files with byte-identical model inputs can reuse the same prior neural output. This is not grouping arbitrary files by filename or assuming a policy result is an AI decision.

The report and progress log distinguish:

- `observed_regular_files`: files actually encountered;
- `model_assessed_files`: files assigned a validated model result;
- `fresh_model_inferences`: new neural forward calls;
- `reused_model_decisions`: assignments from an exact-input cached result;
- `model_assessed_protected_files`: protected files assessed **before** the guard veto;
- approved files, roots finished, inaccessible paths and explicit exclusions.

Fresh + reused equals model-assessed. We do not call reused assignments fresh inference or claim the model read file contents.

On cancellation, cached decisions and an unfinished checkpoint persist. Starting again **re-enumerates the filesystem** and reuses matching decisions; it does not resume an unchecked stale path cursor. Review identity is refreshed. The assessment epoch is retained for a resumed run's age input and is reported separately from the new inventory start time. A first full pass over millions of files can take a long time; later passes avoid repeat neural work for unchanged inputs.

## Storage reporting

Status uses observed allocated bytes, not an assertion of exact physical-exclusive APFS space. The `% of observed bytes` label and `~`/`+` indicators expose partial coverage. These percentages are not percentages of Apple's System Data category. Native category totals retain their source and recorded timestamp independently.

## Verification, without claiming an unfinished pass finished

On the development Mac, a completed read-only **traversal-only** check reached **7,008,034 regular files**, **1,422,532 directories** and **185,997 symlinks** across six roots in about 778 seconds, with permission/boundary issues. This was not a seven-million-file neural review.

A real-model validation run was deliberately interrupted by the **validation harness** after 900 seconds: **746,119 regular files assessed**, comprising **12,054 fresh inferences** and **734,065 exact-input cached assignments**. `walk_finished` correctly remained false. The product itself has no 900-second cutoff. A restart check verified cached reuse and unfinished status. **A completed neural pass over all seven million files has not been claimed.**

Raw paths, checkpoints and private reports are excluded from the public repository. Small hermetic tests complete full fixture scopes, including more than the former 600-file cap and protected files. Native privilege boundaries are tested without collecting a user password.
