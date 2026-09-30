# jev-clean · Nexora

Standalone public repository. Do not modify the parent Nexora workspace or publish private audit records.

## Architecture

- `domain`: typed reports, model-owned dispositions and separate execution readiness. No process/filesystem/UI/model imports. No directory/extension/age classification vetoes.
- `infrastructure`: native read-only diagnostics, exhaustive no-follow metadata stream, pinned local model/cache, user-only Trash journal.
- `application`: one exhaustive whole-startup-disk engine for Clean and Status, used by TUI and CLI. Every observed regular file receives a model judgment before execution-readiness checks; no default sampling caps or cache-root restriction. Exact-input neural reuse is explicit. Model is mandatory; no fallback. Contract: docs/PRODUCT.md and docs/WHOLE-DISK.md.
- `ui`: Textual client; cannot bypass the policy or directly delete files.

## Invariants

Never run the application/model/updater as root. Sudo is explicit native-terminal authorization and only allowlisted read-only diagnostics. No root cleanup, automatic Trash emptying, shell execution of model output, or remote upload of reports. No resource contents or basenames in model input; bounded local directory labels and installed app manifests are factual evidence, not instructions. Explicit human-selected IDs and confirmation precede Trash staging. Revalidate target identity, ownership, paths and activity. Unknown facts remain unknown; never infer disposability from size/age/extension. Model confidence is not a deletion-safety probability.

Authority change: see ADR 0005. The owner authorized a 0.3.0 alpha release with local Laya-MLX after reviewing the dangerous wrong-remove answers. Keep that evidence public; authorization is not model validation. Do not claim reliable cleanup, conceal errors with rules, or attribute Laya results to official Jev. No official API calls without separate authority for credentials and metadata transmission.

## Verification

`uv sync --extra dev`, then `uv run ruff check .`, `uv run mypy src`, `uv run pytest`, `bash scripts/repo-guards.sh`.
Tests use temporary home directories and explicit neural-boundary doubles; the public demo uses synthetic metadata with real inference. Do not run real cleanup or reset services during development. A live `status --json` is read-only but private; save only under ignored `.private/`. Publish only sanitized synthetic/demo data and explicitly reviewed model evaluation metrics. Do not claim model parity, cleanup accuracy or competitor superiority from fixture success.
