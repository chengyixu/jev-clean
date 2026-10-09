# Usefulness investigation — 2026-10-09

Status: diagnosis plus narrow source fixes, **not a released speed/resource redesign**.
The installed v0.3.0 remains unchanged. No live cleanup or full-disk rescan was
performed for this investigation. No monitors or delegated agents were used.

## Reported failure

The user reports hours of jev-clean scanning and mostly KB-scale rows, whereas
an installed Mole run completed in minutes and reported 42.25 GB tracked cleanup,
807 items and a 53.59 GB free-space increase. Those are distinct measurements;
this is not independent evidence of exactly 60 GB of exclusive reclaim. Repeated
Chrome incomplete-download labels can describe different files; repetition alone
is not proof of double counting. No such claim is made here.

## Confirmed causes

1. **Inference is tied serially to individual filesystem entries.** The most recent
   completed private checkpoint records 6,872,755 assessed regular files,
   1,047,674 fresh calls and 5,825,081 reused decisions. It has 1,034,694 selectable
   proposals, 409,052 review assignments and 521,616 permission/I/O events.
   These are counters, not unique inaccessible paths or safe cleanup targets.
   Checkpoint timings for the most recent 512 stored decisions had a median of
   28.13 ms and mean of 28.86 ms; applying this rate to the entire pass would be an
   extrapolation, not measured total model time. Huge decision counts are not
   proof of effective reasoning. No saved per-file report was found in the private
   state root; the total bytes behind the user's KB complaint cannot be reconstructed
   from these counters alone.
2. **Weak resource context.** EvidenceCollector only observes filesystem facts and
   bounded installed application manifests. References and regenerability are
   always unknown. No authoritative package-manager reference graph, build-state,
   download-state or device-support retirement probe exists. Deep input paths
   previously retained only the final four directory components: deep cache and
   project paths could produce identical states. A RED regression proved that
   collision. The source fix retains bounded enclosing and leaf directory context,
   with a new input-contract namespace. It does not invent disposability.
3. **Bad review ordering and unclear totals.** Model removal/review candidates were
   appended and rendered in traversal order. A small-first fixture reproduced
   large proposals being buried. Source now uses one size-ordering function for
   engine and TUI; selection and model answers are unchanged. Progress and summary
   report proposed allocated bytes separately from selected bytes, not freed bytes.
4. **Wrong cleanup unit.** The executor supports regular-file Trash staging only;
   it cannot retire resource bundles or offer typed owner-native cleanup actions.
   It also serializes/replaces the entire cumulative JSON journal twice per file,
   an increasing cost for large selected sets. No journal throughput measurement
   was done here; this is an implementation risk, not an attributed scan bottleneck.
   Trash staging deliberately does not reclaim space. Mole's direct cleanup is
   therefore not equivalent to jev-clean's current receipt.

## Read-only measurements

Eight named resources were measured with native `du -sk`, three concurrent readers,
no inference/deletion, completing in **5.59 seconds**. Current allocations included:
app caches 2.54 GB, uv cache 3.06 GB, pnpm store 6.99 GB, Gradle caches 4.68 GB.
DerivedData was nearly empty, consistent with a post-cleanup snapshot but not proof
of a particular operation. Device Support remained 14.35 GB; that is not automatically
obsolete or disposable. Measurements are private and deliberately not published as
file lists. These roots can overlap other future measurements and are not a promised
reclaim total or proven Apple System Data membership.

## Real model batching experiment

Pinned Laya-MLX 0.2.0, same weights/questions, 24 synthetic structured states from
`scripts/evaluate_model_authority.py`. Used the installed runtime's prepare,
collate and synchronized forward functions; three repeats at each batch size:

| Batch | Median for 24 | Inputs/s | Decision mismatches vs serial |
| ---: | ---: | ---: | ---: |
| 1 | 1.4520 s | 16.53 | 0 |
| 4 | 0.7896 s | 30.39 | 0 |
| 8 | 0.8607 s | 27.88 | 0 |
| 16 | 0.8857 s | 27.10 | 0 |

Batch 4 was about 1.84× faster on this small experiment. Maximum probability
change in the final repetition was about 0.00254 (0.254 percentage points).
This is not exact numeric parity, general decision parity, or an end-to-end speed
promise. The application's production inference path is not yet batched. Its
upstream `batch_size` batches questions within one state, not independent file
states. Native per-state batching needs an explicit adapter and broader regression
cases, including near ties, different lengths, cancellation and memory limits.
Neither batching nor better labels fixes the known classification errors (ADR 0005).

## Narrow-fix verification

Baseline gates: 156 tests, 80.21% coverage. New regression tests were observed RED
before changes, then GREEN. Final working-tree and isolated source-snapshot/fresh
locked Python 3.12 runs: **159 tests, 80.28% coverage**, lint, types and repository
guards passed. Real synthetic inference confirmed deep locations now differ, but
both example answers remained keep: improved input context is not a cleanup-quality
claim. No remote CI, commit, release or installed update was performed.

## Required design change, not implemented by these fixes

- Whole-disk **scope** must be separated from an obligatory per-file neural pass
  before any useful result. The current contract promises every observed regular
  file an individual model-derived assignment. Replacing that with model-owned
  resource decisions is a deliberate contract change, not something to conceal
  as a cache optimization or a sampling cap.
- First measure resource-sized units and their allocation, references, active use,
  generating tool/version and rebuild/download cost. Use a complete coverage ledger
  so unknown/unvisited storage remains explicit. Directory labels alone do not
  justify treating all descendants as one disposable unit.
- Model selects investigative actions and keep/review/remove proposals. Typed
  discovery adapters locate and report resources; **they do not hardcode trash
  classifications** or override the model. Drill into uncertain/mixed resources.
- Surface size-ranked resource results progressively; preserve explicit selections,
  cancellation, target identity/manifests and final human confirmation. Bound UI
  memory without silently dropping findings; a million-row in-memory table is not
  a usable review interface.
- Execution must distinguish reversible resource staging from owner-native pruning
  and permanent cleanup. New actions need explicit human approval and truthful
  receipts, before/after free-space readings and failure reporting. No auto-empty
  Trash, arbitrary model shell code or root model process.
- Benchmark time to first substantive findings, total metadata/inference time,
  model decision errors, overlap-free bytes and proposal correctness. Test named
  large resources against mixed-content/source/credentials fixtures. Never use
  '156 tests passed' or artificial GB fixture counts as evidence of real usefulness.

## Skills/source review

`/find-skills` found `grepug/skills`' macos-dev-storage-cleanup and
`wshobson/agents`' python-performance-optimization. Read their skill docs and the
former's target reference; neither was installed or executed. They support
resource-level measurement, explicit plans and profiling, but their deterministic
risk classes/allowlists are not adopted as model-overriding policy. Remote discovery
is not trusted executable code. The first grepug file fetch used the wrong path and
failed; the verified path was `skills/macos-dev-storage-cleanup/SKILL.md`.

Installed Mole 1.56.0 was inspected read-only to verify behavior: native tool cache
pruning, incomplete-download cleanup and per-project/generated-resource operations.
Mole is GPL-3.0. No source code, algorithms or assets were copied into this Apache-2.0
repository, and its cleanup command was not run. Implementation must be independent
and justified against upstream owner-tool contracts and resource evidence.
