<p align="center"><img src="docs/assets/hero.svg" alt="jev-clean · Nexora — Clean mysterious macOS System Data." width="960"></p>

# jev-clean · Nexora

**Clean the mysterious “System Data” on your Mac—with a local model doing the investigation.**

[![CI](https://github.com/chengyixu/jev-clean/actions/workflows/ci.yml/badge.svg)](https://github.com/chengyixu/jev-clean/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-6ce5ca)](LICENSE)
![Apple Silicon](https://img.shields.io/badge/platform-Apple%20Silicon-172832)
![Local inference required](https://img.shields.io/badge/inference-required%20%26%20local-6ce5ca)

macOS calls hundreds of gigabytes **System Data**. That label doesn't tell you what the data is, why it exists, or whether you can remove it.

**Clean is the flagship System Data workflow.** The terminal stays simple:

```text
1. Clean
2. Status
```

**Clean:** sudo or not → whole startup-disk scan + model assessment → select files → delete or cancel.

**Status:** whole startup-disk scan + model assessment → usage bars and percentages.

**Model-only cleanup.** The model alone decides keep/review/remove; no directory, extension or retention rule can veto that judgment. Execution still verifies the exact selected target and your confirmation. Known limitation: a 24-scenario diagnostic answered 16/24 with structured input and included two incorrect-remove answers, so **review every proposed file**. See [ADR 0005](docs/adr/0005-model-owned-judgment.md) and [model-authority-evaluation.json](docs/model-authority-evaluation.json).

**Not a cache sample anymore.** Both modes walk the mounted startup-disk scope. Every observed regular file gets a model-derived keep/review/remove judgment. Technical execution readiness is recorded separately. No default 600-file, six-directory or two-minute cutoff. Progress separates scanned files, model-assessed files, fresh neural calls and exact-input reused decisions. [Scope, restart/cache behavior and verification](docs/WHOLE-DISK.md).

No dashboard, banners, permanent captions or competing panels. The accounting and full model evidence remain in the shared engine and JSON report, not plastered over the screen.

Laya prioritizes volume inspection, classifies the evidence, and proposes what to keep or remove. You see the actual choices and scores as they happen. You approve the files. Code cannot override that judgment using directories, extensions or retention rules; execution still verifies the selected target and permissions.

> **Alpha software.** No model = no Clean or Status operation. There is no rules-only fallback. Model scores are **not deletion-safety guarantees**. Begin with the real-inference demo and review [SECURITY.md](SECURITY.md). The project name does not imply affiliation with TypeSafe AI; the shipped engine is Laya-MLX.

<p align="center"><img src="docs/assets/walkthrough.gif" alt="Real jev-clean TUI: model decisions, selection and disk breakdown" width="960"></p>

*Historical v0.2.0 TUI walkthrough with real local inference and synthetic filesystem metadata. It illustrates navigation, not v0.3.0 model answers. This is a screen sequence, not real-time playback. No private files or canned neural scores.*

## Two modes. The model drives both.

| | **Clean** | **Status** |
|---|---|---|
| Question | “What can I remove to tackle mysterious System Data?” | “Where is the space actually going?” |
| Model’s job | Prioritize volumes → assess every observed regular file → propose remove / review / keep | Assess the full filesystem scope → classify storage → expose unresolved areas |
| Tools’ job | Stream filesystem metadata, not recommendations | Inventory full scope; collect native/APFS evidence |
| Your control | Select all approved items or some; review and confirm | Read-only investigation; narrow the next scope |
| Result | System Data context + model findings + selected cleanup + receipt/undo | Private JSON report and model decision trace |

**The loop:** model prioritizes → tools walk every declared root → model assesses factual evidence → you review. `?` marks further investigation, `!` an execution-unavailable removal proposal; only model-remove checkboxes can be selected. Esc pauses; restarting re-enumerates with exact prior decisions reused. The first full pass over millions of files can take hours. The file mover supports current-user regular files with unchanged identity and no-follow paths. It never classifies trash. Autonomous dependency investigation and resource grouping are not yet implemented.

### Honest about the gray bar

Where available, jev-clean reconciles a same-timestamp native record:

```text
Used space − macOS − named categories = System Data (“Other”)
```

The displayed System Data number is labeled **macOS log + recorded time**. Press `S` for its exact bytes/source/timestamp. It is a native historical reading, not a hardcoded total or a promise of instant freshness.

It keeps that accounting separate from filesystem allocation. Nested directories overlap; sparse VM files and APFS clones complicate reclaim estimates. Large folders are **not automatically proven members of System Data**. Unavailable native logs, permissions gaps and unexplored branches remain visible. No invented “263 GB explained” headline.

## Install

Requires **Apple Silicon macOS** and `python3` to run the installer. It provisions uv if needed, an isolated Python 3.12 app environment, and the required model automatically. The underlying MLX runtime declares macOS 14+ support; live inference is tested here on macOS 27.0. Intel Macs and Linux cannot run the application model.

```bash
d="$(mktemp -d)" && curl -fL https://github.com/chengyixu/jev-clean/releases/download/v0.3.0/install.py -o "$d/install.py" && python3 "$d/install.py"
jev-clean
```

**One install flow: app → pinned model (~0.85 GB) → checksum verification → real inference test → Ready.** No separate model-setup command. The installer exits with failure if the model cannot be provisioned or run; it never calls an app-only installation complete. Review the [installer source](install.py) and release checksums if desired. It prints the exact launch path if your uv executable directory is not on PATH.

No API key, cloud inference, account, daemon, password capture or sudoers change. Run the installer and app **without sudo**. After installation, inference is local. Advanced direct-package installs also automatically provision missing weights on the first Clean/Status operation; network/download failure stops the operation, never produces a fallback.

### Try the model without touching your files

```bash
jev-clean clean --demo
jev-clean status --demo
```

The demo feeds synthetic disk metadata through **real mandatory Laya inference**. It cannot move real files. An incomplete model cache is provisioned automatically; failed provisioning stops the operation.

### Permission flow

Clean asks **“Use sudo?”** with Yes/No; No is the default. Yes returns to the real terminal for `sudo -v`. Passwords never enter Python, the agent or the model. Cancelling starts no scan. Status goes straight to read-only agent logs and results. Sudo broadens read-only evidence—not deletion power—and does not bypass SIP, TCC or Full Disk Access.

## Agent skill and JSON CLI

The agent skill uses the exact same engine and safety boundaries. Install/link the [skill directory](skills/jev-clean) using your agent's skill manager, then invoke `/jev-clean` or ask it to inspect disk usage.

```bash
jev-clean status --json
jev-clean status --json --root "$HOME/Library/Application Support"
jev-clean clean --json --root "$HOME/Library/Caches" \
  --output "$HOME/.local/state/jev-clean/review.json"

# Optional deeper native READ access: human authenticates in their own terminal.
sudo -v
jev-clean status --deep --json

# ONLY after the human reviews and approves these particular IDs:
jev-clean apply "$HOME/.local/state/jev-clean/review.json" \
  --ids ID1,ID2 --confirm TRASH
```

`--root` selects an explicitly labeled custom scope, not deletion permissions. With no `--root`, the entire mounted startup-container scope is attempted. The JSON `system_data` section carries native total/residual, source/time, candidate bytes and attribution limits for **both** modes. `exploration.stats` separates observed files, protected files, model decisions and approved candidates. Zero approvals does not mean “nothing to clean.” It can reflect missing evidence, model error/retention or execution limits. Plans expire in one hour. Every chosen file needs a `remove` decision and technical staging readiness; applying a plan collects fresh evidence, re-runs model assessment and checks identity/activity. Invalid or missing model output stops the operation. Reports contain private paths: **do not upload them**.

## Controls and utilities

| Key | Action |
|---|---|
| `1` / `2` | Clean System Data / Status |
| `↑ ↓` or `j k` | Navigate |
| `← →`, then `Enter` | Choose Yes/No in the sudo and deletion questions |
| `S` | Show exact native System Data bytes, source and recorded timestamp |
| `Space` | Toggle a model-approved, safety-checked file |
| `A` / `N` | Select all visible approved / select none |
| `/` | Filter paths |
| `Enter` | Clean: confirm selected files with Yes/No; Status: open a directory |
| `R` | New model investigation |
| `E` | Export private report |
| `H` | History and undo instructions |
| `U` | Check release updates |
| `?` / `Esc` / `Q` | Help / back or cancel / quit |

Status percentages are shares of **observed allocated bytes in non-overlapping groups**—not percentages of Apple's System Data category or exact APFS-exclusive physical space. `~`/`+` marks partial coverage; missing values stay unknown. Permission gaps and unmounted volumes remain explicit. Enter opens an already measured child breakdown or asks the model to investigate that directory. Details and utility shortcuts are available on demand, not in a permanent footer.

```bash
jev-clean doctor
jev-clean history
jev-clean restore BATCH_ID --confirm RESTORE
jev-clean update           # check only
jev-clean update --apply   # confirm update; model provision + inference verified before ready
jev-clean completion zsh   # also bash and fish; prints, doesn't modify shell config
```

The deletion question defaults to **No**. Only an explicit Yes proceeds with the selected paths and the existing model/safety rechecks.

**Trash is not free space.** Staging is reversible; it does not immediately reclaim bytes. jev-clean never automatically empties Trash. Restore refuses to overwrite an existing file.

## Why Laya-MLX?

Laya is a typed-decision encoder: one bounded question goes in, a choice distribution comes out. No token-by-token prose or model-generated shell code. The pinned [aac6fef/laya-mlx](https://huggingface.co/aac6fef/laya-mlx) checkpoint runs natively with MLX on Apple Silicon.

We researched the English, multilingual and typed-decision Laya families plus open Jev reproductions. “Jev” search results are not a single interchangeable model. See [the source-linked research](docs/RESEARCH.md), [architecture decision](docs/adr/0001-local-decisions.md) and [product contract](docs/PRODUCT.md).

### What the measurements actually say

Historical v0.1/v0.2 evidence: a local 12-case synthetic-metadata diagnostic produced **7/12 exact expected choices**. None of the nine protected/uncertain fixtures became selectable; **that is the combined model-plus-veto result, not proof that the model is safe**. Model proposals can be wrong. The diagnostic is small, hand-authored and related to prompt-development examples—not an independent accuracy benchmark. Raw outputs, timings, mismatches and limitations are published in [model-evaluation.json](docs/model-evaluation.json).

Version 0.3.0 evidence: the 24-scenario structured-input diagnostic answered **16/24**, with **two false-remove answers**, including a unique private key and required offline model weights. No type veto masks these errors. These small authored examples are not an accuracy benchmark; the results were reviewed and accepted before release. Reproduce with `uv run python scripts/evaluate_model_authority.py --output .private/authority.json`.

We do not claim superior cleanup accuracy to Mole or that local inference understands every file. The distinction is a visible, mandatory model-driven investigation and a strict human-controlled execution boundary.

## Safety scope

- No root deletion, recursive tree deletion, app uninstallation or automatic Trash emptying.
- Databases, VM disks, model weights, source work, credentials and backups are not blanket cleanup targets.
- Read/model scope is the whole mounted startup disk. No cleanup root, extension or retention classifier overrides the model.
- Current-user regular-file staging checks canonical paths, owner, device/inode/size/mtime/ctime/link count and refreshed activity.
- Unknown activity is model evidence; unavailable exact target metadata is an execution limitation, not a keep judgment.
- Model decisions are mandatory. Only valid remove answers with technical staging readiness can be selected.
- Same-user concurrent writers remain a race risk. Close relevant apps before cleanup. See [threat model](SECURITY.md).

## Develop / reproduce

```bash
git clone https://github.com/chengyixu/jev-clean.git
cd jev-clean
uv sync --frozen --extra dev --python 3.12
uv run bash scripts/verify.sh
uv run python scripts/evaluate_model.py --output docs/model-evaluation.json  # cold cache provisions automatically
uv run python scripts/capture_demo.py
```

Hermetic tests use temporary directories and an explicit neural-adapter test double; the application has no fake-model switch. Real-inference evaluation and media capture automatically provision a missing checkpoint, just like the app. On macOS, PNG/GIF rendering needs Cairo discoverable (e.g. `DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"`). The SVG screenshots do not require Cairo.

## License and credits

Apache-2.0. A **Nexora** project. Laya by Convai Innovations; independent MLX port by mizorewww/aac6fef. Mole's documented interface informed the research; no Mole source or artwork was copied. See [NOTICE](NOTICE).
