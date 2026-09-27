# Product contract — jev-clean · Nexora

Current owner scope (2026-09-27) supersedes the initial four-mode/optional-model sketch.

## Two modes, one mandatory model

1. **Clean**: load local Laya → ask for terminal sudo diagnostics → gather initial filesystem observations → model chooses directories to inspect → bounded tools return metadata → model classifies storage and proposes remove/review/keep → safety veto → user selects all or some approved candidates → final confirmation → model re-assesses selection → identity/open-file recheck → user Trash + receipt/undo.
2. **Status**: load local Laya → terminal sudo diagnostics → native category/APFS grounding → model chooses deeper directory breakdown → tools measure those locations → model labels the storage → show evidence, explicit coverage gaps and native System Data reconciliation. No mutation.

No Analyze/Optimize modes. No `--model off`, rules-only fallback or canned neural scores. The model chooses discovery and recommends cleanup, not just post-processes a deterministic scan. Missing weights, failed load/inference or invalid predictions stop the operation. Pure administrative commands (`help`, `version`, `model setup`, `update`, `history`, `restore`) do not invent model outputs; restore is recovery, not a new deletion decision.

## Boundaries

The filesystem tool is not an oracle: it enumerates and measures. Laya is a bounded typed-decision encoder, not a generative planner. It selects inspect/skip, storage purpose, and removal disposition through fixed typed options. Unknowns and budget exhaustion are visible. It cannot invent new commands, read contents, or alter a measurement. Read scope is HOME plus selected native system/library roots. `--root` narrows investigation; it is not a deletion allowlist.

Safety checks are vetoes only: a deterministic check cannot recommend deletion or select an item without a `remove` decision. Only model-approved plus safety-approved files can be selected. Scores are displayed as model distributions, not calibrated safety guarantees. Default selection is empty. No arbitrary threshold is marketed as proof of correctness. Open-file and identity rechecks remain mandatory.

Demo mode changes only the file metadata input. It uses the real pinned model for exploration/classification/disposition, is visibly labeled synthetic data, and cannot mutate real files. Hermetic CI tests substitute the external neural adapter explicitly; that test mechanism is not available as an application flag.

## Honest scope

Version 0.1 stages only stale regular files in bounded disposable roots. Model discovery may find databases, VM disks, model caches and backup archives; they are shown as evidence, not erased to reduce a chart. Per-directory bytes and Apple's Storage categories remain separate. APFS shared/sparse/compressed blocks and concurrent writes make exact reclaim and per-file System Data membership unavailable in many cases. Report these limits instead of claiming to account for every gray-bar byte.
