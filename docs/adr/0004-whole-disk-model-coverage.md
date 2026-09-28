# ADR 0004: Exhaustive scope, inference before veto

Accepted 2026-09-28. The owner rejected cache-root discovery and the 412-model-file result as insufficient. This supersedes the bounded sampling design, not the permission/deletion safeguards.

Default scope comes from the startup APFS container. Mounted roots are attempted fully, without default file/directory/scan-time cutoffs. Native filesystem metadata streaming does not read file contents. Python no-follow descriptor traversal is used without elevation; fixed native `find -x … -print0` and ordinal `stat` metadata commands provide elevated read access when authorized. No root Python or model process.

Every observed regular file gets a validated neural decision before safety policy. System/source/database/credential files are no longer removed from the model queue because a rule already vetoes their deletion. A whole-disk scan can therefore assign millions of protected decisions while still offering a small safe mutation set.

Exact identical inference inputs can reuse the pinned model's previous output through a private cache. Counters distinguish observed files, assessed files, fresh calls, reused assignments, protected assessments and approvals. Incomplete scans retain a checkpoint and cache; restart re-enumerates current paths and refreshes identities. Model input age uses the recorded assessment epoch for restart consistency. No stale iterator offsets or file IDs authorize deletion.

All I/O gaps and intentional exclusions are explicit. The scanner's state is excluded to avoid a changing self-generated inventory. External filesystems and unmounted snapshots are not silently mounted; the intended scope is accessible mounted startup-container filesystems, not a raw forensic read of every disk sector. A completed traversal can still have gaps.

Whole-disk work costs time. Verification must distinguish a completed metadata traversal from a completed model-assignment pass, and fresh neural calls from exact-state reuse. No synthetic success or bounded sample may be advertised as a complete real disk review.
