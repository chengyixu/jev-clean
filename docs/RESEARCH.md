# Research notebook — macOS System Data and typed decisions

Research date: 2026-09-27. This is a source-based engineering decision, not a clinical or statistical deletion-safety certification. No private machine paths, filenames, or audit records are published here.

## Decision

Ship **jev-clean · Nexora** with a Python/Textual TUI and JSON CLI sharing one policy engine. Local **Laya-MLX English** (`aac6fef/laya-mlx`, revision `20aed815fc6acde75733882e7ec0e3f28aeb9717`) is the mandatory decision engine on Apple Silicon. The owner explicitly rejected a model-optional implementation: missing/failed inference stops Clean and Status; there is no rules-only fallback. The current two-mode scope is specified in [PRODUCT.md](PRODUCT.md). No automatic network download during scans: model setup is explicit. No hosted inference or file-content upload.

Removal state is bounded English metadata, without file contents or filenames. Exploration additionally uses bounded local directory-label hints, treated as untrusted data. The model selects which locations to expand, classifies their purpose, and assesses discovered files. A three-way `choice` question offers `remove`, `review`, `keep`. The output is a mandatory model recommendation, not a probability of safe deletion. Only `remove` plus a hard-guard pass permits user selection; no confidence cutoff is presented as proof of safety. Explanations come from measured facts and the rules; they are not invented Laya chain-of-thought. The app exposes actual inference timing and all option probabilities. The hard safety veto runs before and again at execution, independently of the model. User confirmation remains mandatory.

## Models researched

| Candidate | Primary evidence | Decision |
|---|---|---|
| Laya English | ModernBERT-large, 421M parameters, 512-token combined question/state context; Apache-2.0 [1] | English metadata fits; use MLX port on Apple Silicon |
| Laya multilingual | mmBERT, 322M; default 1,024 tokens, upstream optional 8,192; Apache-2.0 [2] | Not default. Card explicitly reports overconfidence and near-chance zero-shot typed decisions; English metadata avoids language-routing hazards |
| aac6fef/laya-mlx | FP16 independent MLX port; Python 3.11+, macOS 14+, arm64; no PyTorch needed [3,4] | Selected. Pin weights/runtime; load safetensors; no remote repository code |
| Open Jev DeBERTa | Independent, not affiliated with TypeSafe; Apache-2.0; banking/sentiment/BoolQ training; 512 context; model card notes out-of-domain weakness [5] | Research comparator, not a macOS deletion oracle; not shipped in this release |
| Other HF “jev” results | Search returns multiple unrelated/reproduction repos [6] | Do not silently treat a search term as a trusted model identity |

Upstream MLX reports ~13.4 ms one-question median and ~944 MiB peak allocation on its M3 Max. These are **upstream benchmark figures**, not jev-clean measurements or promises [4]. Its 63/63 selected-answer parity evaluates port fidelity, not correctness of disk cleanup recommendations. Laya multilingual explicitly states that a confident answer can be wrong [2]. We make no claim that Laya is superior to Mole or deterministic cleanup policies on deletion safety. Local evaluation must report errors, disagreements and abstentions, not only latency.

## Storage investigation

Apple defines System Data as files outside more specific Storage categories [7,8]. On the development Mac, read-only `StorageManagementService` logs exposed `StorageLogInvestigation` records. In a complete same-timestamp record, `Used - System - sum(named categories)` exactly equaled `Other`. This is machine/version-specific evidence, **not a public stable API**. Documents and Other changed asynchronously. Storage amounts from different timestamps cannot be subtracted as if they were one snapshot.

Consequences:
- Parse complete timestamp groups only. Never fill missing categories with zero or merge separate snapshots. If logs are unavailable, show `unavailable`, not an invented gray-bar breakdown.
- `du -x -k` measures allocated blocks in a filesystem, not Storage category membership. APFS clones/hard links/compression, sparse VM disks, permissions and live writes prevent exact exclusive-reclaim promises. Never sum overlapping roots.
- Show category totals separately from filesystem evidence. Filesystem items have **unattributed category membership** unless a provider explicitly proves it.
- APFS Data snapshots and System/update snapshots are different. Discover them read-only; never delete update snapshots or swap files. Sudo does not grant Full Disk Access or override SIP/TCC.
- Logs, caches, model weights, databases, VM images and backups are not interchangeable. A 64 GB running database is data, not garbage.

## Mole comparison and product scope

Mole's GPL-3.0 README documents Clean, Optimize, Analyze, Status, uninstall/purge/installer/history/update, keyboard selection and safeguards [9]. We studied behavior and documentation; **no Mole source or assets are copied**. This is an independently implemented Apache-2.0 project, not a compatible replacement for every Mole command.

jev-clean differentiators: timestamp-consistent category reconciliation; explicit unknowns; local typed-decision probability trace; private JSON plans for agents; file-level conservative eligibility; human selection; reversible staging in Trash; identity checks and audit/restore. Version 0.1 has **Clean and Status only**. It deliberately does not uninstall apps, erase models/databases, prune Docker volumes, empty Trash, or claim performance gains from maintenance. No Analyze/Optimize commands are shipped.

## Security / permission design

Run the TUI as the ordinary user. Each of its two main actions offers deeper diagnostics. The TUI temporarily returns control to the real terminal for `sudo -v`; password input is never read by Python, a model or an agent. Elevated subprocesses are a short allowlist of native **read-only** diagnostics (`du`, `diskutil`, `log`). There is no root Python helper, root inference, model-provided command, sudo deletion, or permanently installed daemon. Cancelled/failed authorization returns without starting; users may explicitly select unprivileged diagnostics, with visible coverage gaps. This is not a model-free mode.

Only stale regular files in a small enumerated set of regenerable cache roots, rotated-log roots, and app log roots can pass the delete gate. Symlinks (including ancestors), hard links, current files, database/credential/source/archive-like files, external mounts, another owner's files, active files and unknown open-file status are vetoed. Directory trees themselves are never recursively deleted. Executing an exported plan revalidates rules and identity, never trusts a saved `eligible` flag. A selected file moves to user Trash, so the UI reports **staged**, not “space freed.” Undo cannot overwrite existing source files. No tool can prove total safety against an adversarial concurrent filesystem mutator; document the remaining race and prefer closing applications before cleanup.

## Required evaluation

- Unit: residual reconciliation, malformed/incomplete groups, age gates, model result parsing, scope and probability validation.
- Filesystem: symlink/ancestor swap, hardlinks, active/unknown open files, changed inode/mtime, forged plan, root/path traversal, permissions, all/partial selection, cancellation, Trash/restore collision, crash journal.
- TUI: two modes, arrows/j/k, Space, select-all model-approved and guard-approved only, search, help, confirmation, cancellation, resizing, real screenshot export from synthetic file metadata with real inference.
- Integration: CLI JSON roundtrip, fresh install, private permissions, read-only macOS scan; real local model smoke and small diagnostic fixture benchmark. Publish dataset/method/limitations; no cleanup accuracy claims from a tiny hand-curated set.

## Sources

1. https://huggingface.co/convaiinnovations/laya — publisher card; accessed 2026-09-27.
2. https://huggingface.co/convaiinnovations/laya-multilingual — publisher architecture, limits and calibration warnings; accessed 2026-09-27.
3. https://huggingface.co/aac6fef/laya-mlx — independent conversion card, license/provenance; accessed 2026-09-27.
4. https://github.com/mizorewww/laya-mlx and https://pypi.org/project/laya-mlx/ — runtime API, dependency/compatibility and upstream benchmark methodology; accessed 2026-09-27.
5. https://huggingface.co/com-kotobalabs/open-jev-deberta-v3-large — publisher explicitly disclaims TypeSafe affiliation and cross-domain guarantees; accessed 2026-09-27.
6. https://huggingface.co/api/models?search=jev&sort=trendingScore&limit=10 — discovery only, not an endorsement.
7. https://support.apple.com/en-us/102624 — Apple, Free up storage space on Mac.
8. https://support.apple.com/guide/mac-help/see-used-and-available-storage-space-sysp4ee93ca4/mac — Apple Storage category descriptions.
9. https://github.com/tw93/mole — upstream README inspected via GitHub API; GPL-3.0, feature/safety comparison only.
10. https://eclecticlight.co/2026/09/02/caches-and-purging-in-macos-tahoe/ — independent macOS specialist; supplementary context, not file-level classification evidence.

Network access was intermittent during research; HF model cards, PyPI metadata and GitHub READMEs were retrieved successfully after retries. Search-result marketing claims about “safe System Data deletion” were not accepted as evidence.
