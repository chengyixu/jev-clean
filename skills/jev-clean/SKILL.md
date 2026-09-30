---
name: jev-clean
description: Use jev-clean's mandatory local model to investigate macOS System Data, discover potential trash, and prepare explicit human-reviewed cleanup. Two modes, Clean and Status; no model-free fallback.
---

# jev-clean · Nexora

Use the installed CLI; it is the same engine as the TUI. Check `jev-clean --version` before assuming 0.3.0 behavior. ADR 0005 records known real-model errors and the owner's alpha-release authorization; never present that authorization as validated cleanup accuracy. The actual backend is local Laya-MLX, not official TypeSafe Jev.

## Setup and investigation

```bash
jev-clean doctor
jev-clean status --json
jev-clean clean --json --output "$HOME/.local/state/jev-clean/review.json"
```

The normal installer provisions and verifies the model automatically. No separate setup command. Direct-package installs also provision missing weights on first operation (about 0.85 GB); downloading or inference failure stops the operation. Once cached, inference is local. There is no `--model off`, rules-only mode, Analyze or Optimize command.

Clean is the flagship **mysterious macOS System Data cleanup** flow: native accounting → model-directed contributor investigation → model file decisions → user review → cleanup receipt. Its `system_data` context is not exclusive to Status. Status provides the read-only deeper breakdown. The TUI is intentionally minimal: Clean → sudo or not → agent logs → files → Yes/No deletion. Status → logs → measured usage bars. No persistent dashboard or investigation toggle; detailed accounting remains in JSON. Without `--root`, both modes attempt the whole mounted startup APFS scope, with no default file/directory/duration cap. Every observed regular file receives a model judgment. In 0.3.0, classification is model-only; execution readiness is separate. `--root /path` explicitly selects a custom scope; never call it whole-disk coverage. It does not authorize deletion. Permission/unmounted/external/symlink/scanner-state gaps remain explicit.

For deep native diagnostics, the human runs `sudo -v` in their terminal first, then `jev-clean status --deep --json`. Never collect or pipe a password, run the whole app as root, or send credentials to a model. Sudo does not grant Full Disk Access/TCC.

## Explain evidence

Read `coverage`, `exploration.stats`, `exploration.steps` and `exploration.nodes`. `observed_regular_files` and `model_assessed_files` are file counts; `fresh_model_inferences` and `reused_model_decisions` distinguish new calls from exact-identical-input cache reuse. Never present reuse as fresh inference or metadata review as content inspection. `walk_finished` does not mean complete coverage when gaps remain. Cancellation persists the decision cache; restarting re-enumerates paths and reuses matching results. Scores are model distributions, not deletion-safety guarantees. Laya does not generate explanations: show the evidence and actual typed choices, not invented chain-of-thought.

Read `categories.timestamp`, `used_bytes`, `system_bytes`, `named`, `other_bytes` together. The native figure is a recorded log reading, not instantaneous usage; `system_data.source` and `timestamp` identify it, and the TUI's S key shows provenance. `exploration.stats` explains observed/protected/model-assessed/approved counts. Never interpret zero approved files or an exhausted budget as a clean disk. Residual = used - system - sum(named). Never mix timestamps. Directory allocation is **not** proof of System Data category membership; measurements are explicitly unattributed. Native logs are private/version-dependent and may be unavailable. Whole-disk percentage rows show observed allocated-byte shares with partial indicators, not exact APFS-exclusive space or shares of Apple's category. Do not sum unrelated or nested snapshots.

## Human authority

Show each proposed path, size, measured facts, actual model choice and separate execution issue. Only a valid model `remove` plus technical staging readiness is selectable. `review` is visible but not selectable; do not pretend its dependency investigation has been completed. Do not infer disposal from a directory, extension or fixed age. Never bypass model keep/review or choose targets yourself just to shrink a chart. Human selection and confirmation remain mandatory. Known model failures remain disclosed; do not conceal them with filesystem-type rules.

After the human approves specific IDs, and only then:

```bash
jev-clean apply "$HOME/.local/state/jev-clean/review.json" --ids ID1,ID2 --confirm TRASH
```

The engine requires a working model again, re-assesses selection, and checks scope, identity and open handles at execution. Plans expire after one hour. Never fabricate approval, blanket-select IDs yourself or bypass failures. Report skipped items. Files move to user Trash; **no space is freed by staging**. Do not empty Trash automatically.

## Recovery and utilities

```bash
jev-clean history
jev-clean restore BATCH_ID --confirm RESTORE
jev-clean update
```

Restore is a user-requested recovery operation and cannot overwrite an existing source file. Update is check-only; applying it requires separate interactive terminal confirmation. Help/setup/history/recovery are administrative operations, not substitute cleaning modes.

Reports and journals contain private paths. Never upload them or raw logs to GitHub or a remote model. `--demo` uses synthetic filesystem metadata with **real local inference**, cannot remove real files, and is appropriate for public demonstrations.
