# Product contract — resource-first jev-clean

Current local development version: **0.4.0.dev2**, not a published release.
[ADR 0006](adr/0006-resource-first-cleanup.md) supersedes per-file neural assessment
as the default. Whole-startup-disk scope does not mean one AI call for every file.

## Two modes

- **Clean:** sudo Yes/No → native resource measurements and mandatory model decisions
  → largest-first resources → select → seal selected membership and reassess → final
  Yes/No explicitly including directory descendants → revalidate and stage in Trash.
- **Status:** same resource inventory → disjoint allocated-byte shares → Enter on a
  directory to inventory its children. No deletion.

Clean results are checkbox-only: `[ ]` and `[x]`, path, size, selection totals. Only model-approved, independently evidenced and execution-ready items appear. No `?`/`!` status rows, blocked-item counts or scan-gap banners. Diagnostics and unselectable decisions remain in the private JSON report; hiding them never authorizes removal. Empty results say "No items to select", not "disk is clean".

No new mode or dashboard. The default enumerates disjoint boundaries across the
mounted startup APFS scope; explicit `--root` is custom scope. Known filesystem/home
containers are expanded only to choose useful measurement units, not to classify
trash. Every accessible sibling remains represented. Native subtree totals cover
opaque trees; descendants do not each receive a separate model call.

Four native measurement workers have 30-second per-resource deadlines. Failed or
timed-out measurements remain unknown/non-actionable. No total-resource sampling
cap. Scope-finished differs from complete access: symlinks, filesystem boundaries,
unmounted volumes, scanner-state exclusion and permission gaps stay explicit.
Directory frontier enumeration is unprivileged even when native du uses sudo.

## Model and evidence

Pinned local Laya-MLX is mandatory. Missing/error inference stops the operation,
with no rules-only fallback. Inputs contain bounded enclosing/leaf directory labels,
measured allocation/activity and installed-app manifest facts, not user file contents or
arbitrary file basenames. The exact 43-byte cache declaration header is read for evidence. Directory names are not instructions or proof of garbage.
Unknown dependencies/regenerability remain unknown. Whole-directory questions have
keep/review/remove options. Raw answers remain auditable, but **remove alone cannot authorize cleanup**. Independently observed valid CACHEDIR.TAG cache declarations are currently required, with exact covered scope and marker identity revalidated before staging. Untagged personal/mixed/unknown data remains unselectable regardless of raw model answer. See [ADR 0007](adr/0007-evidence-backed-cleanup.md); no folder-name blacklist or confidence threshold.

Exact serialized resource input + questions + label mapping + input contract +
model/runtime key the private cache. Fresh and reused counts are separate. Counters
say resources, not individual files. Proposed bytes are not selected/freed bytes,
exclusive APFS reclaim, or proven Apple System Data membership. Native System Data
retains its independent recorded timestamp and provenance.

## Execution

Directory decisions concern the whole subtree. Selected resources are sealed with
a no-follow descendant metadata digest before final confirmation (and before an
actionable CLI plan export). Exact target identity, membership, ownership and activity
are rechecked at apply/staging. Overlapping targets and executor-state conflicts are
refused. Directories move atomically into journaled user Trash; undo cannot overwrite.
No recursive permanent deletion, owner-native pruning, root cleanup or automatic
Trash emptying. Staging alone frees no space. Existing regular-file undo is retained.

Same-user concurrent writers remain a race risk; close writers and retain backups.
Model errors remain known and resource-level accuracy is not validated by speed tests.
Review unfamiliar large directories; do not approve them solely to achieve a GB total.

## Installation and measurement

Automatic pinned-model provisioning/checksum validation/real readiness inference
remain. A local preview uses `python3 install.py --source .`; published v0.3.0 retains
its previous behavior. Demos use synthetic metadata and cannot mutate user data.
Resource measurements and test methodology are in ADR 0006 and VERIFICATION.md.
