---
name: jev-clean
description: Use jev-clean's mandatory local model to investigate macOS System Data, discover potential trash, and prepare explicit human-reviewed cleanup. Two modes, Clean and Status; no model-free fallback.
---

# jev-clean · Nexora

The model drives discovery, not just labels. Use the installed CLI; it is the same engine as the TUI.

## Setup and investigation

```bash
jev-clean doctor
jev-clean status --json
jev-clean clean --json --output "$HOME/.local/state/jev-clean/review.json"
```

The normal installer provisions and verifies the model automatically. No separate setup command. Direct-package installs also provision missing weights on first operation (about 0.85 GB); downloading or inference failure stops the operation. Once cached, inference is local. There is no `--model off`, rules-only mode, Analyze or Optimize command.

Clean is the flagship **mysterious macOS System Data cleanup** flow: native accounting → model-directed contributor investigation → model file decisions → user review → cleanup receipt. Its `system_data` context is not exclusive to Status. Status provides the read-only deeper breakdown. In the TUI, B inside Clean switches investigation/file review while the System Data panel stays visible. `--root "$HOME/Library/Caches"` narrows either investigation's read scope when a broad exploration exhausts its budget. It does not authorize deletion. Investigations are bounded and incomplete coverage is explicit; do not call unvisited data empty.

For deep native diagnostics, the human runs `sudo -v` in their terminal first, then `jev-clean status --deep --json`. Never collect or pipe a password, run the whole app as root, or send credentials to a model. Sudo does not grant Full Disk Access/TCC.

## Explain evidence

Read `exploration.steps` for actual model inspect/skip decisions and `exploration.nodes` for measured/model-classified locations. Scores are model distributions, not deletion-safety guarantees. Laya does not generate explanations: show the evidence and actual typed choices, not invented chain-of-thought.

Read `categories.timestamp`, `used_bytes`, `system_bytes`, `named`, `other_bytes` together. Residual = used - system - sum(named). Never mix timestamps. Directory allocation is **not** proof of System Data category membership; measurements are explicitly unattributed. Native logs are private/version-dependent and may be unavailable. Nested directory rows overlap and must not be summed.

## Human authority

Show the user each proposed path, size, age, actual model choice and guard reason. Only `remove` + guard pass is selectable. Do not bypass model `keep`/`review` decisions. Protected databases/models/VMs/backups/credentials/source work must not be erased just to shrink the chart.

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
