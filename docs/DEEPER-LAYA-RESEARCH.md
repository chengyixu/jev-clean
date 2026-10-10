# Deeper Laya cleanup research and local runtime candidate — 2026-10-10

This follows LAYA-LEARNING.md's failed frozen-encoder/head experiments. The user
requested actual Laya improvement, not path/tag disposal gates. Work is direct,
on-device, no external model/teacher, subagents, monitors, private uploads or real
cleanup. Local candidate is 0.4.0.dev3; publication/installation must be verified,
not inferred from this document. No universal safe-deletion claim.

## Primary-source findings

1. **Train the representation, not only the readout.** Laya's upstream fine-tuning
   guide says head-only freezing fits small hardware but gains less than full tuning.
   Published default training uses encoder and head learning rates, many more updates,
   held-out calibration and optional option shuffling. We verified the native installed
   MLX ModernBERT implementation (28 layers, 1024 hidden dimension) can differentiate
   through encoder-tail layers. Full-backbone adaptation/LoRA was considered but not
   needed for these bounded experiments; four-tail-layer adaptation was implemented.
2. **Option order is a real failure dimension.** Upstream Laya reports option-reversal
   errors and lower sensitivity after fine-tuning/shuffling. Published selection-bias
   literature supports counterbalancing and learning debiasing, but its decoder-model
   measurements are not direct proof for Laya. We measured Laya's own reordered
   choices, added all six orderings and selected checkpoints on reordered development
   cases rather than canonical answers only. A batched mean of mapped distributions
   is the final learned inference rule, not a folder blacklist or confidence veto.
3. **Unknown and distribution shift need explicit evaluation.** Calibration changes
   confidence, not argmax correctness. Selective-classification literature warns that
   source-distribution guarantees do not automatically survive shifted deployment.
   No calibrated deletion-safety probability, conformal guarantee or arbitrary runtime
   threshold is claimed. Corpus labels include unknown/mixed/active/needed controls.
4. **Actual operations matter.** uv's official cache contract says it is NEVER safe
   to modify its cache directly; use native `uv cache prune`. pnpm provides native
   `store prune` for unreferenced packages and a distinct force mode that removes alien
   files. No force mode is used. This invalidates whole-directory Trash cleanup of
   owner-managed caches, even if the data is regenerated. Such semantics are inputs
   for Laya; executable owner operations are fixed verified tool interfaces, never
   model-generated commands.
5. **Raw names can be instructions, not evidence.** Actual candidate testing reproduced
   a false remove from an injected label asking the model to choose A. The classifier
   now receives typed immediate-entry structural observations, activity and verified
   tool facts, NOT arbitrary directory labels, absolute paths or application IDs.
   Display paths remain in private reports/UI. Renaming a folder cannot change this
   model state. Structural samples explicitly do not establish subtree purity,
   unique original status or regeneration. No content reads or imaginary facts.

## Sources (primary unless noted)

- [1] Laya upstream [fine-tuning guide](https://github.com/NandhaKishorM/laya/blob/1adc59f7e371deb601fcfa18a14e25db238addcc/docs/finetune.md)
  and [train implementation](https://github.com/NandhaKishorM/laya/blob/1adc59f7e371deb601fcfa18a14e25db238addcc/laya/train.py).
  Author's results are task-specific; no cleanup accuracy inferred from them.
- [2] [Native Laya-MLX](https://github.com/mizorewww/laya-mlx), installed 0.2.0
  model/agent/common source inspected. No silent runtime/model/provider swap.
- [3] [ModernBERT paper](https://aclanthology.org/2025.acl-long.127/) and
  [mlx-raclate training](https://github.com/pappitti/mlx-raclate/blob/2a85e79035da8f6fc06cfd865639ed5e5a16cdb5/README.md).
  The latter is an implementation reference, not used as an extra runtime dependency.
- [4] [LoRA](https://arxiv.org/abs/2106.09685), method researched but not applied here.
- [5] [Teacher–Student General Permutation Debiasing](https://aclanthology.org/2024.findings-acl.81/)
  and [Order/Token Selection Bias](https://aclanthology.org/2024.findings-acl.333/).
  No external teacher used; findings guide test design only.
- [6] [Selective Classification Under Distribution Shifts](https://arxiv.org/html/2405.05160v2).
  Peer-reviewed-method context; no guarantees transferred to this tiny corpus.
- [7] uv [official cache safety/cleanup docs](https://github.com/astral-sh/uv/blob/4efeeaf5704ddbfda8cb4f6d08deb7a4ce1f81d7/docs/concepts/cache.md)
  and installed `uv cache prune --help` (read only).
- [8] pnpm [official store documentation](https://pnpm.io/cli/store) and installed
  `pnpm store --help/path` (read only). One initial help invocation caused Corepack to
  fetch its configured pnpm version; subsequent probes disable Corepack network/download
  prompts. This was not a prune or data-cleanup operation.

`/find-skills` found Laya integration / native decision-model workflows; reviewed
Laya-specific guidance from wdobry/laya-playground, not installed. Remote skill
marketing about calibrated probabilities was not accepted as a safety guarantee.
Two reference fetches used nonexistent paths/ref and failed; corrected sources
above, not empty files, support the findings.

## Experiment progression — raw predictions, no permission gates

All data are authored English synthetic observations, not independently reviewed
filesystem ground truth. Families and exact texts are separated. Names Pictures,
Documents, Downloads/cache/generated/opaque occur across ALL labels in training;
no learned label simply equals a path. Synthetic positive facts (verified originals,
owner confirmation/reference checks) are richer than current general collectors.

| Run | Change | Main observed result |
| --- | --- | --- |
| Tail-2, seed0 | 150 cases, last2encoder layers+head/scorer, 300 updates | 48-case holdout 39/48, 0 false removes,15/16 disposable detected; new30case set had1false remove and option orders exposed8/180 |
| Tail-4 expanded, seed1 | 300 cases, all6orders,600updates | Canonical new30case0false remove, but reordered4false removes; still unacceptable |
| Robust dev, seed2 | Select on6orders (108dev-layout cases) | Ensemble41/48 and26/30,0false removes; observation-format holdout still had credential false remove |
| Observation-trained, seed3 | 444cases, factual structural/action examples,label smoothing | Ensemble45/48 and27/30,0false removes; observation-format unknown credential still failed |
| Action records, seed4 | 572cases,30dev families/layout variants | Useful prune recall improved; uv direct removal became a false remove in observation set |
| Action-question, seed5 | Change question from neededness to proposed-action support | Worse raw base and trained development errors; not selected |
| Balanced longer, seed6 | Resume factual model;1800updates,batch6,3×training cost on unknown/needed examples,all6orders,4tail layers | Observation24set22/24,0false removes,7/7 cleanup positives; diagnostic41/48 and27/30,0false removes |

Balanced run: **75,278,337 actual native Laya parameters**, 56 changed tensors.
Question/operation records plus shuffled target remapping verified. Optimizer budget:
3,432 layout items,10,800 examples seen (~3.15 layout passes). The measured
balanced optimizer time was **961.530s**, total feature/training run **1078.338s**
under machine contention. Earlier smaller runs undertrained relative to this budget.
The trained artifact is the same ModernBERT/Laya architecture, not a replacement LLM.

All earlier holdouts became exposed as results were inspected and subsequent datasets
were authored. They are now DIAGNOSTIC, not repeatedly called untouched tests. Final
admission tests were frozen AFTER candidate selection, before those records were run.
The first32case final caught label injection (1false remove). Typed label-free contract
addressed the generic input attack, not a path exception; that rerun is diagnostic.

## Fresh label-free final and packaged inference

A new24case final was frozen before any inference. Typed structural/unknown, active/
unique, mixed, owner-direct-removal and owner-native prune cases:

- **22/24 correct, zero false removals**.
- **6/8 useful cleanup positives** recognized; misses: uv native prune wording and
  generated compiler objects. Keep-everything cannot count as success.
- Native package-loaded FP16 artifact exactly reproduced the research decisions.
- This small authored holdout is not population safety calibration. All exposed sets
  now require a fresh independent final for future tuning. No universal guarantee.

Trained artifact provenance:
`jev-cleanup-laya-encoder4-balanced-v1`, FP16 selected update360/seed6;
SHA256 **7602f928e0926e0bde7cae2ed40fb83432a3cfd33834c6d150b46ca59a20d310**,
150,562,387 bytes. Pinned base revision20aed815fc6acde75733882e7ec0e3f28aeb9717.
The installer needs the verified local adapter; missing/corrupt adapter stops before
Ready, no base-model fallback. No private path or API key in the artifact metadata.

## Current runtime candidate

- Learned Laya ensemble owns keep/review/remove. CACHEDIR.TAG is observation only;
  path/tag-based admission removed. Existing canonical metadata/privacy/manifest checks
  still protect execution, not classification.
- Generic observation record uses bounded immediate samples, excludes arbitrary names,
  never claims unique-data/references from suffixes alone. No basenames/content uploads.
- Model can propose owner-native uv/pnpm prune from installed path discovery/help/
  documented semantics and current process visibility. The classifier is not a command
  generator; only fixed owner-tool actions can be executed. Unknown/missing discovery
  produces no fabricated contract. Process detection ignores only the scan's own
  ancestry; another running owner process remains visible and execution blocks conflicts.
- Owner actions are assessed first. Generic startup inventory still continues without
  a total-resource sample cap. Opaque data often defers, as it should. That limits current
  useful coverage; no 27GB speculative folder-total cleanup claim is retained.
- Checkbox label for native operation is `uv cache prune` / `pnpm cache prune`.
  Final Yes/No explicitly states native pruning **cannot be undone** and sizes are
  allocated upper bounds. CLI requires CLEAN for plans containing native pruning,
  TRASH only for reversible staging. Fresh owner observation and model reassessment
  precede execution; plan/model cannot supply arbitrary argv or force flags.
- Trash file/resource staging retains exact manifests/identity, pre-confirmation review,
  no-overwrite recovery and current-user execution. No root deletion or automatic
  Trash emptying. No user cleanup was run during research/testing.

## Actual read-only observations and performance

- Typed trained classifier on real Pictures/Documents/Desktop/Downloads/Models roots:
  review, no raw remove. Generic caches/logs defer without sufficient role/use facts.
- A validation startup pass was cancelled by harness at210s:1508resources assessed,
  no personal proposals, incomplete. This exposed bad sequencing; owner actions moved
  first. Not an end-to-end full-disk completion or universal speed claim.
- Revised six explicit roots: **161resources in15.390s**,0measurement gaps;
  **zero personal folders selectable**, two model-approved native opportunities:
  uv ~3.064GBallocated upper bound and pnpm currentv11store20KB. Native prune may free
  only a subset. Older pnpm generations remain unverified, not silently erased.
- Option ensembles on small synthetic cases measured ~40–200ms/resource as load varied.
  Exact-input reuse remains tied to adapted artifact/question/input schema; no child-file
  inference claim and no stale old-model-cache reuse.

## Final performance follow-up

A read-only installed startup validation was interrupted at240s,1698resources,
36measurement gaps. It is retained as an incomplete performance regression, not
claimed completed. Corrective changes: 10s per-resource native deadline with explicit
gaps, and allocation/age kept in report/display rather than redundant learned-model
cache input. Size alone cannot establish need; actual structural/activity/tool facts
remain distinct. New exact-input namespace invalidates earlier state reuse.

Revised source startup inventory: **2047discovered,2029measured,18read failures,
46incomplete measurements,165.385s**, declared scope finished but full access false.
Two learned owner-native opportunities, no personal-folder checkboxes,~3.065GB store
allocation upper bound. No cleanup executed. 36 actual-runtime semantic controls
still produced no raw removes after the size-independent change. More measurements
can time out; this is an explicit coverage tradeoff, not false zero/full-access.

The local preview does not claim Mole-equivalent GB/minute cleanup across all apps.
It materially improves raw Laya decisions and supported operations; broad unverified
application state continues to defer.

## Final build and installed receipts

**258 software tests**,80.49% local/80.39% fresh source coverage, lint/types/guards
passed. Fresh sdist and locked Python3.12 environment repeated the gates; isolated
and actual installers verified base checksums plus the learned artifact. A final
same-version local installation initially reused a stale wheel; source installs now
force refresh of jev-clean and a RED regression protects that behavior. Final installed
Python files match checkout, CLI reports0.4.0.dev3, model doctor identifies the exact
adapted SHA and marks cleanup probabilities uncalibrated.

Actual installed final custom-scope read-only CLI:53resources,20.915s end-to-end,
zero personal checkboxes,uv/pnpm native opportunities present,10s measurement deadline.
Earlier equivalent run13.786s under different load. No prune or user-data move.
No public release, external CI or personal data publication. Private trained weights
are not included in source archives and require the verified local adapter path.

These tests establish implementation/selected regression behavior, not an independent
real-world safety bound. The user goal across all cleanup classes is not fully solved:
general unverified folders defer, and only observed uv/pnpm operations have owner
execution adapters in this preview.

## Broader owner interfaces verified

Added documented read-only discovery/command semantics for npm cache verify (integrity
verification and garbage collection), pip cache purge, and Go build-cache-only clean.
No npm force-clean, pnpm force mode or Go module/source cleanup. Exact operation labels
appear in checklist and irreversible confirmation. These are typed owner tools, not
folder-disposal rules; learned Laya must approve the actual observed operation.

Live explicit owner-discovered stores plus personal roots: **318 resources, 4 owner
actions assessed, 13.074s, no measurement gaps**. Laya approved uv, Go build cache and
pnpm current store; zero personal proposals. Allocation upper bounds: uv3.066GB,
Go1.114GB,pnpm20KB (~4.18GBcombined), not measured objects removed/exclusive reclaim.
Laya withheld npm. Pip's tool reported a cache path that does not currently exist,
so no target or bytes were invented. No cleanup operation executed. Final local/fresh-source gates: **266 tests,80.50%coverage**. Actual expanded
installed preview check:318resources16.569s,scope finished,0measurement gaps,
0personal proposals,uv/Go/pnpm approved. Verified learned adapter and installed source
parity. Final receipts are in VERIFICATION.md.

## Remaining gaps

Owner-native actions cover five verified tool interfaces, not all Mole categories. Old tool stores,
Xcode device support, browser downloads, application state and logs need generating-tool
observations or richer measured purpose—never inferred disposable from names. A model
cannot recover missing unique-data/dependency facts from a size total. Independent user-
reviewed ground truth, more languages, drift/adversarial tests, probability calibration
and broader app contracts remain needed. No premise that every cache must be proposed
or every unreferenced-looking resource is garbage. No guarantee of risk-free deletion.
