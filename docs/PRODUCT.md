# Product contract — jev-clean · Nexora

Current owner scope (2026-09-27) supersedes the initial four-mode/optional-model sketch.

## Flagship: clean mysterious macOS System Data

Clean includes native System Data accounting, model-selected contributor investigation, cleanup proposals, user review and receipts in one workflow. It is not a generic cleaner with System Data confined to Status. The `system_data` JSON context retains native accounting and attribution limits. The latest owner UX direction removes the dashboard: a plain two-item menu; Clean asks sudo Yes/No, shows flowing logs, then file selection and a Yes/No deletion question. Status shows logs, then non-overlapping usage rows with bars and percentages. No permanent banner, multiple panels or B investigation toggle. Moving to Trash does not reduce disk usage; no reduction of Apple's gray bar is assumed.

## Installation is complete only when the model runs

The official installer installs app/runtime, downloads missing pinned weights, checks SHA256 integrity, and runs real inference before Ready. There is no second model setup command. Direct-package installs automatically provision a cold cache on first operation. Download, hash or inference failures stop the flow rather than claiming partial readiness. Confirmed updates verify the installed model too.

## Two modes, one mandatory model

1. **Clean**: load local Laya → ask for terminal sudo diagnostics → gather initial filesystem observations → model chooses directories to inspect → bounded tools return metadata → model classifies storage and proposes remove/review/keep → safety veto → user selects all or some approved candidates → final confirmation → model re-assesses selection → identity/open-file recheck → user Trash + receipt/undo.
2. **Status**: load local Laya → read-only native category/APFS grounding → model chooses deeper directory breakdown → tools measure those locations → model labels the storage → show evidence, explicit coverage gaps and native System Data reconciliation. No mutation.

No Analyze/Optimize modes. No `--model off`, rules-only fallback or canned neural scores. The model chooses discovery and recommends cleanup, not just post-processes a deterministic scan. Missing weights, failed load/inference or invalid predictions stop the operation. Pure administrative commands (`help`, `version`, `doctor`, `update`, `history`, `restore`) do not invent model outputs; restore is recovery, not a new deletion decision.

## Boundaries

The filesystem tool is not an oracle: it enumerates and measures. Laya is a bounded typed-decision encoder, not a generative planner. It chooses the next concrete directory from measured/observed options, classifies storage purpose, and decides file removal disposition through fixed typed options. It is no longer asked to binary-skip all vague roots before any facts exist. Unknowns and budget exhaustion are visible. It cannot invent new commands, read contents, or alter a measurement. Read scope is HOME plus selected native system/library roots. Clean offers concrete user storage/cache/log locations to the model, then inventories metadata in each chosen location and spends inference on files not already vetoed by safety checks. Status collects native directory measurements without spending a model call on every immediate entry, then the model prioritizes deeper reads. Slow HOME children are measured independently so one stalled directory cannot hide all others. `--root` narrows investigation; it is not a deletion allowlist.

Safety checks are vetoes only: a deterministic check cannot recommend deletion or select an item without a `remove` decision. Only model-approved plus safety-approved files can be selected. Scores are displayed as model distributions, not calibrated safety guarantees. Default selection is empty. No arbitrary threshold is marketed as proof of correctness. Open-file and identity rechecks remain mandatory.

Status percentages use fully measured siblings at each displayed level. Nested children do not inflate parent totals; completed children are promoted when an incomplete ancestor would hide them, with an explicit unmeasured gap. Partial sizes are retained with `+`, and unknown percentages stay `?`. These are measured-row shares, not shares of Apple's category or a claim to know every allocated block. Native System Data totals carry their recorded time and source; `S` opens provenance. Empty Clean results distinguish zero assessed, model-kept, safety-vetoed and incomplete discovery instead of declaring the disk clean.

Demo mode changes only the file metadata input. It uses the real pinned model for exploration/classification/disposition, is visibly labeled synthetic data, and cannot mutate real files. Hermetic CI tests substitute the external neural adapter explicitly; that test mechanism is not available as an application flag.

## Honest scope

Version 0.1 stages only stale regular files in bounded disposable roots. Model discovery may find databases, VM disks, model caches and backup archives; they are shown as evidence, not erased to reduce a chart. Per-directory bytes and Apple's Storage categories remain separate. APFS shared/sparse/compressed blocks and concurrent writes make exact reclaim and per-file System Data membership unavailable in many cases. Report these limits instead of claiming to account for every gray-bar byte.
