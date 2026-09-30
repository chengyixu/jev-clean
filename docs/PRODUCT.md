# Product contract — jev-clean · Nexora

Version 0.3.0 release contract, authorized after disclosure of the model-evaluation risk. See [ADR 0005](adr/0005-model-owned-judgment.md) for the model-authority decision and its known accuracy limits. Whole-disk scope, minimal UI and automatic model-ready installation remain.

## Two modes

1. **Clean:** sudo or not → exhaustive accessible startup-filesystem metadata walk → model decision for every observed regular file → model-owned keep/review/remove → explicit all/partial user selection → Yes/No → re-assessment and identity/open-file checks → user Trash and undo.
2. **Status:** same exhaustive accessible startup scope and model assessment → observed-byte groups and model classification → simple percentage rows. No deletion.

The model prioritizes volume order, but cannot use “skip” to omit the rest of an explicitly requested disk scan. There is no default file, directory or total-duration cap. `--root` explicitly changes scope and is labeled custom. Native read timeouts/errors are gaps, not zeros or completion.

## Entire disk, not “412 eligible files”

The full observation stream includes system/data/VM/preboot/recovery/update volumes when mounted in the startup APFS container, with boot snapshot/firmlink aliases deduplicated. All **regular files** reach mandatory model assessment before mutation eligibility. Symlinks, special entries, permission failures, unmounted/locked volumes, external mounts and the scanner's own growing state have explicit coverage accounting. See [WHOLE-DISK.md](WHOLE-DISK.md).

No resource contents or basenames enter removal inference. Bounded local directory labels, extensions, installed app ID/version matches and filesystem observations form the input. Unknown dependencies/regenerability remain explicit. Application manifests are bounded metadata reads; an ID match does not prove ownership. A private SQLite cache reuses outputs only for exact identical model input/question/model/runtime identities. Fresh neural calls and reused assignments are shown separately. Rerunning after cancellation walks the filesystem again with cached neural decisions, not stale file identities.

“Walk finished” and “complete coverage” are separate. Native System Data is still a timestamped residual, not a folder or a deletable target. Observed-byte percentages do not prove Apple's category membership or exclusive APFS reclaim.

## Model readiness

The official installer installs runtime, provisions pinned weights, verifies SHA256 integrity and performs inference before Ready. Missing/error inference stops an operation; no rules-only fallback. Direct package installs self-provision on first use. Administrative help/history/restore/update operations do not fabricate inference.

## Authority and safety

The model alone decides disposition. There are no path/extension/age/open-handle/hard-link trash-classification vetoes. Technical staging readiness is separate: the executor supports current-user regular files, requires unchanged target identity and canonical no-follow paths, and cannot move its own journal/Trash. Model review rows remain visible but not selectable. Unknown activity is evidence, not automatic keep. Current evidence is collected again for mandatory re-inference before staging; changed identities require renewed review. No root deletion, automatic Trash emptying or arbitrary model-generated shell commands. Every selected file is confirmed by the user. Trash staging alone does not free space.

Not yet implemented: resource-level grouping, autonomous investigation of review rows, and authoritative application dependency/version-retirement probes. Do not label basic manifest observations as these capabilities. The bundled model is known to be imperfect; human review is the primary safeguard.

Demo uses synthetic metadata with real inference and cannot mutate real files. Tests substitute only external neural boundaries; no production fake-model flag exists.
