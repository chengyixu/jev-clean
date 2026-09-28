# jev-clean · Nexora

Standalone public repository. Do not modify the parent Nexora workspace or publish private audit records.

## Architecture

- `domain`: typed reports + deterministic, fail-closed policy. No process/filesystem/UI/model imports.
- `infrastructure`: native read-only diagnostics, exhaustive no-follow metadata stream, pinned local model/cache, user-only Trash journal.
- `application`: one exhaustive whole-startup-disk engine for Clean and Status, used by TUI and CLI. Every observed regular file is model-assessed before guards; no default sampling caps or cache-root restriction. Exact-input neural reuse is explicit. Model is mandatory; no fallback. Contract: docs/PRODUCT.md and docs/WHOLE-DISK.md.
- `ui`: Textual client; cannot bypass the policy or directly delete files.

## Invariants

Never run the application/model/updater as root. Sudo is explicit native-terminal authorization and only allowlisted read-only diagnostics. No root cleanup, automatic Trash emptying, database/VM/model deletion, shell execution of model output, or remote upload of reports. No file contents or arbitrary filenames in model input. Explicit human-selected IDs and confirmation precede Trash staging. Revalidate scope, age, identity, ownership, open handles. Unknown coverage is a veto, not zero bytes. Model confidence is not a deletion-safety probability.

## Verification

`uv sync --extra dev`, then `uv run ruff check .`, `uv run mypy src`, `uv run pytest`, `bash scripts/repo-guards.sh`.
Tests use temporary home directories and explicit neural-boundary doubles; the public demo uses synthetic metadata with real inference. Do not run real cleanup or reset services during development. A live `status --json` is read-only but private; save only under ignored `.private/`. Publish only sanitized synthetic/demo data and explicitly reviewed model evaluation metrics. Do not claim model parity, cleanup accuracy or competitor superiority from fixture success.
