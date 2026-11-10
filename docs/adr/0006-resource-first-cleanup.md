# ADR 0006 — Resource-first investigation and selected-resource manifests

Status: implemented, verified and installed locally as 0.4.0.dev0; not a published release.
The user explicitly requested a fast, efficient replacement for the hours-long
file-level architecture. Supersedes ADRs 0004/0005 only for assessment granularity
and execution units. Mandatory local Laya, human confirmation, no root execution,
private evidence, and the two-mode UI remain.

## Why

A completed v0.3.0 scan assessed 6.87 million files with 1.05 million fresh model
calls and over a million selectable rows. Counts are not useful cleanup. Batching
24 synthetic inputs improved inference by about 1.84x; it cannot turn that design
into a minutes-scale review. See USEFULNESS-INVESTIGATION.md for the baseline.

## Design

1. Discover the mounted startup scope as before (or explicitly requested roots).
   Construct disjoint resource boundaries by expanding filesystem/home organizational
   containers, aliases and scanner-state ancestors. Every accessible sibling is
   represented; location rules set **granularity, not disposability**. Symlinks,
   unmounted volumes, inaccessible frontiers and filesystem boundaries are explicit.
   Since 0.4.1, after measuring a home directory resource, one throttled native
   `find` lists validated `CACHEDIR.TAG` declarations inside it. If any exist, the
   scan opens only their ancestors with the same discovery walker, so each outermost
   declared cache becomes its own resource and every resulting resource is judged.
   The parent is not judged as well. A declaration changes granularity only; it is
   never approval. Search deadlines are reported as declaration search gaps.
2. Four native read-only `du -x -k -s` workers measure directory resources, with
   throttled disk I/O (`taskpolicy -d throttle`, which execs `du` in place). Direct
   files use stat. Each native job has a 30-second deadline and cancellation. A
   deadline is recorded as an incomplete measurement, never zero/full coverage.
   There is no total-resource sample cap. Resource boundary enumeration and native
   measurement do not read file contents. No Python object/model call per descendant.
3. Model decides keep/review/remove for each resource. Its question explicitly
   concerns the **whole directory**, including mixed/unknown contents. Model choices,
   exact-input reuse, resource totals, time and coverage remain visible. No rules-only
   fallback or directory/extension deletion allowlist. No claim that every child
   received an individual neural judgment.
4. Results are largest-first. Since 0.4.0.dev1, Clean shows only selectable checkbox
   rows. Review/unavailable rows and diagnostics remain in JSON, not the list;
   technical inability does not rewrite model judgments. No automatic selection. Startup log lines show
   results as native jobs finish; the final review table opens after the inventory.
   No separate new mode or dashboard. Status enters a directory to inventory its
   children with the same engine.
5. **After selecting, before Yes/No**, capture a descriptor-based metadata manifest
   of each selected directory and rerun the model. The dialog explicitly says ALL
   descendants are included. No resource is moved without its reviewed manifest.
   Changed membership, symlink ancestors, foreign owners, filesystem crossings,
   special entries, duplicate/overlapping selections and transaction-state conflicts
   are refused by execution mechanics, not relabeled as keep.
6. At apply, refresh metadata/activity and verify manifests, rerun the model, then
   recheck the manifest and root identity at staging. Atomically rename the whole
   directory to a journaled Trash batch; restore with atomic **no-replace** rename
   (Darwin renameatx_np / Linux renameat2). Symlinks inside a tree move as links and
   are never followed. Existing regular-file journals/restore remain supported.
   Directory exports also seal manifests before writing an actionable CLI plan.

The old per-file engine remains a diagnostic comparison module and regression
fixture target, not the default production path and not a silent fallback.

## Important boundaries

- Native measured bytes are allocated subtree totals, not exclusive APFS reclaim.
  Cross-resource hard links/clones may share blocks. Trash staging frees no space;
  permanent cleanup/owner-native pruning and auto-emptying are not added here.
- A directory with many descendants costs extra at selected review and apply.
  This deliberate metadata work is no longer paid for millions of unselected
  files, and it uses no per-child inference. Exports of all proposals may be slow
  because they seal every actionable resource.
- No validated cleanup accuracy claim. Laya previously made dangerous false-remove
  decisions. Resource grouping increases the importance of reviewing the whole
  target. A measured 27 GB of removal proposals does not mean 27 GB is disposable.
  App-native reference/dependency knowledge is still limited.
- Concurrent same-user writers can race the final check/rename. This is not a
  filesystem snapshot or protection against a same-user adversary. Close writers,
  retain backups and do not select unfamiliar resources just because they are large.
- Scope-finished and complete access differ. Frontier enumeration itself is
  unprivileged; sudo permits native measurements, not root inference or deletion.
- Memory (0.4.1): the model runs with no MLX buffer cache; the default cache grows
  toward RAM size with variable-length inputs. New measurements pause at kernel
  "warn" memory pressure and the scan stops like a cancel at "critical", keeping
  measured results and marking the inventory incomplete. There is no external
  memory guard process; reports record process memory per stage.
- One run per user (0.4.1): an advisory `flock` on `~/.local/state/jev-clean/run.lock`
  refuses a second TUI, scan, apply or model check. SIGTERM unwinds like Ctrl-C, so
  native readers stop and none outlives the process.
- Owner-managed stores (0.4.1): a Trash target equal to, inside or containing a store
  that an owner tool manages is unselectable; only the owner-native operation applies.
- Changed input contracts use a separate namespace/cache from v0.3.0 decisions.
  No warm-start speed claim is labeled cold inference.

## Measurements (development Mac, read-only, 2026-10-09)

- Eight explicit storage roots: **175 resources, 174 fresh calls, 20.391 seconds**
  after model load/open-handle collection; 27.50 GB proposed remove, 6.17 GB review.
  These are real model proposals, not independently validated garbage.
- Startup frontier: **2,020 resources in 0.692 seconds**, six declared roots.
- Cold startup attempt: validation cancelled at **150 seconds**, 1,558 resources
  assessed; 1,471 fresh / 87 reused. Correctly marked unfinished. The validation
  deadline is not a product-wide duration limit.
- Subsequent startup inventory: **90.092 seconds**, all 2,020 resources assessed,
  253 fresh / 1,767 reused, **36 incomplete measurements** plus frontier exclusions.
  Scope finished; complete access false. Timing excludes model load/lsof and native
  category diagnostics. No full-access, end-to-end cleanup or cold-90-second claim.

Final verification: 184 tests, lint/types/guards passed locally and from a fresh source archive. Isolated and actual local installations passed pinned-model readiness; actual installed two-root/18-resource cold CLI Clean finished in 16.902s end-to-end. Installed Python sources matched the checkout. No remote CI/public release for the preview.

No user data was cleaned. Filesystem execution tests use temporary fixtures only.
Private reports are excluded from source control. Public documentation contains
aggregate counters, no user file lists or credentials.
