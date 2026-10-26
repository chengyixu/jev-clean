# Project context

Current release: **0.4.0** (2026-10-26): interactive Status treemap, actual-path Clean, resource-first engine and the v3 learned Laya cleanup adapter. Release history is in CHANGELOG.md and docs/VERIFICATION.md. Check the installed CLI (`jev-clean --version`) and the GitHub release rather than inferring installed or published state from this file.

jev-clean is a standalone Nexora-family macOS tool. Python 3.12+, Textual 1.x; mandatory Laya-MLX 0.2.0 on Apple Silicon macOS 14+. Only Clean and Status are main workflows, both model-driven. Pure/adapter-boundary tests run cross-platform; the application and real-inference demo require Apple Silicon macOS. No backend service, account, or API key is required. Network is used only for model/adapter provisioning, installation and release checks.

## Model provenance

The only home of these pins is `src/jev_clean/infrastructure/model.py`.

- Base checkpoint: `aac6fef/laya-mlx` at revision `20aed815fc6acde75733882e7ec0e3f28aeb9717`, verified against its pinned manifest SHA-256.
- Learned cleanup adapter: `jev-cleanup-laya-runtime-observations-v3`, SHA-256 `5b65d16deeb20ac8c9e6ab43cb3c9fe4478896df8e2326e5744559797546bd33`, published at Hugging Face `ChengyiX/jev-clean-cleanup-adapter` revision `4000ecc1423ba5b17694b14a631abe424a64b002`. It replaces encoder layers 24–27, the final norm, type embedding, decision head and scorer.

Both are provisioned automatically on first use (installer readiness check, `doctor --verify-model`, `update --apply`, or the first Clean/Status operation). The adapter is downloaded into a private staging directory, checksum-verified, then atomically moved to `~/.local/share/jev-clean/models/<adapter-id>/model.safetensors` with mode 0600. A tampered installed adapter is rejected, never silently replaced. Download failure stops the operation; there is no base-model or rules-only fallback.

A new adapter means a new Hugging Face revision plus new ID/SHA/revision pins in `model.py`, with its evaluation recorded in docs. Failed candidates, training corpora and actual-machine audits stay under ignored `.private/`. Training inputs are synthetic path-free observations; never train on or publish real user paths or file contents.

Evaluation numbers come from authored controls, not independent ground truth. The v3 adapter still made one false removal in a 720-question six-order diagnostic. Human selection, exact manifests and final confirmation are the load-bearing safeguards; model probabilities are not deletion-safety probabilities.

## Runtime behavior

Whole-disk scope: default mounted startup APFS container, not just user caches. No total-resource cap; native reads have explicit deadlines and gaps. Every measured resource receives a model judgment; no descendant-file inference is claimed. Exact-input resource decisions are cached and reused explicitly. Esc cancels and leaves no actionable partial plan; restart remeasures resources with exact cached neural reuse. Plan export marks a resource that changed after the scan as unselectable with a rescan issue; selection, confirmation and apply fail closed.

Local runtime data: `~/.local/state/jev-clean/` (private JSON plans/journals and the decision/checkpoint database), `~/.Trash/jev-clean-<batch>/` (staged files), `~/.local/share/jev-clean/models/` (learned adapter), Hugging Face cache (base checkpoint). These are not project artifacts. Never publish an actual machine audit.

## Engineering

Architecture: domain contracts/policy ← infrastructure adapters ← application service ← CLI/TUI. Domain has no I/O. See ADR 0001 and SECURITY.md. The sector profile is locally schema/path validated; the retired OwlSpace map engine is not installed or claimed as validated.

Verify locally with `uv run sh scripts/verify.sh` (Ruff lint and format, mypy, pytest with a 75% coverage floor, architecture guards). There is no hosted CI. Real Apple Silicon model evaluation is an opt-in local script, and results must state hardware/runtime, cold load vs inference, dataset size and errors. Sudo authentication requires a real terminal. No live destructive tests on a user's machine.

Release: one `main` branch. Bump `pyproject.toml`, `install.py` `VERSION`, the `update.py` source fallback and `uv.lock` together (`tests/test_release_consistency.py` enforces this), run `verify.sh` from a fresh worktree, then tag `vX.Y.Z` and publish `install.py`, wheel, sdist and `SHA256SUMS`. `update` checks the fixed GitHub upstream; `--apply` requires terminal confirmation, installs the explicit release tag with uv and verifies model readiness. No automatic installer shell execution.
