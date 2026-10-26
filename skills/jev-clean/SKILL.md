---
name: jev-clean
description: Use jev-clean's mandatory local model to investigate macOS System Data, discover potential trash, and prepare explicit human-reviewed cleanup. Two modes, Clean and Status; no model-free fallback.
---

# jev-clean · Nexora

Release 0.4.0. Use the installed CLI; it is the same engine as the TUI. Check `jev-clean --version` first.

- **Resources, not files.** Native concurrent measurement, one model judgment per resource. `model_assessed_resources` does not count descendant files. A directory proposal includes the ENTIRE subtree; its exact metadata manifest is sealed before human confirmation or plan export and verified again at apply. Native timeouts are coverage gaps. Proposed allocated bytes are not safe or exclusive reclaim. See ADR 0006.
- **Learned Laya v3 adapter.** Path-free typed observations and a reordered probability ensemble; no filename blacklist or tag-required admission. Tags are input facts only; unknown uniqueness and dependencies stay unknown. The adapter is downloaded from its pinned Hugging Face revision and checksum-verified automatically. Review [POSTTRAINING-PARITY.md](../../docs/POSTTRAINING-PARITY.md) and [DEEPER-LAYA-RESEARCH.md](../../docs/DEEPER-LAYA-RESEARCH.md) for raw failures; do not promise deletion safety.
- **Clean** lists actual file/directory paths only. Owner-tool cache operations (uv/pnpm prune, npm verify, pip purge, Go build-cache clean) are technical advisories, are irreversible and distinct from Trash, and need explicit human Yes/No or CLI `--confirm CLEAN` with fresh owner/path/activity checks. Their store allocation is NOT proposed file bytes.
- **Status** draws Apple's category labels as nested treemaps and exposes JSON `storage_map`. Category names do not prove per-file membership: native top-level totals have their own timestamps, path groups are estimates, Unattributed is separate. A selects only known model-approved, execution-ready Trash paths; D runs manifest preparation and the final No-default confirmation. No selection authorizes agent execution without explicit human approval. See docs/STATUS-TREEMAP.md.
- **Plan export** marks a resource that changed after the scan as unselectable with a rescan issue and keeps the rest of the plan; selection, confirmation and apply still fail closed. ADR 0005 records known real-model errors and the owner's alpha-release authorization; never present that authorization as validated cleanup accuracy. The actual backend is local Laya-MLX, not official TypeSafe Jev.

## Setup and investigation

```bash
jev-clean doctor
jev-clean status --json
jev-clean clean --json --output "$HOME/.local/state/jev-clean/review.json"
```

The normal installer provisions and verifies the model automatically. No separate setup command. Direct-package installs also provision the missing model and learned adapter on first operation (about 1.15 GB); downloading or inference failure stops the operation. Once cached, inference is local. There is no `--model off`, rules-only mode, Analyze or Optimize command.

Clean is the flagship **mysterious macOS System Data cleanup** flow: native accounting → model-directed contributor investigation → model file decisions → user review → cleanup receipt. Its `system_data` context is not exclusive to Status. Status provides the read-only deeper breakdown. The TUI is intentionally minimal: Clean → sudo or not → agent logs → files → Yes/No deletion. Status → logs → nested treemap with drill-down. No persistent dashboard or investigation toggle; detailed accounting remains in JSON. Without `--root`, both modes attempt the whole mounted startup APFS scope, with no total-resource cap. Every measured resource receives a model judgment; classification is model-only and execution readiness is separate. `--root /path` explicitly selects a custom scope; never call it whole-disk coverage. It does not authorize deletion. Permission/unmounted/external/symlink/scanner-state gaps remain explicit.

For deep native diagnostics, the human runs `sudo -v` in their terminal first, then `jev-clean status --deep --json`. Never collect or pipe a password, run the whole app as root, or send credentials to a model. Sudo does not grant Full Disk Access/TCC.

## Explain evidence

Read `coverage`, `exploration.stats`, `exploration.steps` and `exploration.nodes`. `resources_discovered`, `resources_measured` and `model_assessed_resources` count resources, not descendant files; `fresh_model_inferences` and `reused_model_decisions` distinguish new calls from exact-identical-input cache reuse. Never present reuse as fresh inference or metadata review as content inspection. `walk_finished` does not mean complete coverage when gaps remain. Cancellation persists the decision cache; restarting re-enumerates paths and reuses matching results. Scores are model distributions, not deletion-safety guarantees. Laya does not generate explanations: show the evidence and actual typed choices, not invented chain-of-thought.

Read `categories.timestamp`, `used_bytes`, `system_bytes`, `named`, `other_bytes` together. The native figure is a recorded log reading, not instantaneous usage; `system_data.source` and `timestamp` identify it, and the TUI's S key shows provenance. `exploration.stats` explains observed/protected/model-assessed/approved counts. Never interpret zero approved files or an exhausted budget as a clean disk. Residual = used - system - sum(named). Never mix timestamps. Directory allocation is **not** proof of System Data category membership; measurements are explicitly unattributed. Native logs are private/version-dependent and may be unavailable. Treemap areas below the top level are observed allocated bytes in estimated category paths, not exact APFS-exclusive space or shares of Apple's category. Do not sum unrelated or nested snapshots.

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
