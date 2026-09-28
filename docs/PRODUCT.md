# Product contract — jev-clean · Nexora

Current whole-disk scope supersedes the cache-oriented bounded discovery in 0.1.x. Minimal UI and automatic model-ready installation remain.

## Two modes

1. **Clean:** sudo or not → exhaustive accessible startup-filesystem metadata walk → model decision for every observed regular file → safety vetoes → explicit all/partial user selection → Yes/No → re-assessment and identity/open-file checks → user Trash and undo.
2. **Status:** same exhaustive accessible startup scope and model assessment → observed-byte groups and model classification → simple percentage rows. No deletion.

The model prioritizes volume order, but cannot use “skip” to omit the rest of an explicitly requested disk scan. There is no default file, directory or total-duration cap. `--root` explicitly changes scope and is labeled custom. Native read timeouts/errors are gaps, not zeros or completion.

## Entire disk, not “412 eligible files”

The full observation stream includes system/data/VM/preboot/recovery/update volumes when mounted in the startup APFS container, with boot snapshot/firmlink aliases deduplicated. All **regular files** reach mandatory model assessment before mutation eligibility. Symlinks, special entries, permission failures, unmounted/locked volumes, external mounts and the scanner's own growing state have explicit coverage accounting. See [WHOLE-DISK.md](WHOLE-DISK.md).

No file contents or arbitrary filenames enter removal inference. Path-derived type/category hints and measured metadata form bounded English inputs. A private SQLite cache reuses outputs only for exact identical model input/question/model/runtime identities. Fresh neural calls and reused assignments are shown separately. Rerunning after cancellation walks the filesystem again with cached neural decisions, not stale file identities.

“Walk finished” and “complete coverage” are separate. Native System Data is still a timestamped residual, not a folder or a deletable target. Observed-byte percentages do not prove Apple's category membership or exclusive APFS reclaim.

## Model readiness

The official installer installs runtime, provisions pinned weights, verifies SHA256 integrity and performs inference before Ready. Missing/error inference stops an operation; no rules-only fallback. Direct package installs self-provision on first use. Administrative help/history/restore/update operations do not fabricate inference.

## Authority and safety

The model decides disposition; deterministic policy can only veto. Protected files are **still assessed**, not hidden before inference. Existing protection for credentials, databases, source work, models, active files and unknown metadata is retained. No root deletion, automatic Trash emptying or arbitrary model-generated shell commands. Every selected file is confirmed by the user and revalidated immediately before staging. Trash staging alone does not free space.

Demo uses synthetic metadata with real inference and cannot mutate real files. Tests substitute only external neural boundaries; no production fake-model flag exists.
