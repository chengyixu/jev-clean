# Project context

jev-clean is a standalone Nexora-family macOS tool. Python 3.12+, Textual 1.x; mandatory Laya-MLX 0.2.0 on Apple Silicon macOS 14+. Only Clean and Status are main workflows, both model-driven. Pure/adapter-boundary tests run cross-platform; the application and real-inference demo require Apple Silicon macOS. No backend service, account, or API key is required. Installation includes automatic pinned-model provisioning and real-inference verification. A cold/incomplete cache also provisions automatically on first operation. No manual model setup is required. Network is used only for these provisioning/install paths and release checks.

Whole-disk scope: default mounted startup APFS container, not just user caches. No default scan cap; all observed regular files reach the model before veto. Exact-input inference cache and counters are described in docs/WHOLE-DISK.md. Esc stops a pass; restart re-enumerates with cached decisions.

Local runtime data: `~/.local/state/jev-clean/` (private JSON plans/journals and `disk-scan/` decision/checkpoint database), `~/.Trash/jev-clean-<batch>/` (staged files), Hugging Face cache (pinned model weights). These are not project artifacts. `.private/` is ignored for local evidence. Never publish an actual machine audit.

Verify with `scripts/verify.sh`. Hosted CI covers Linux and macOS pure/fixture behavior; actual Apple Silicon model evaluation is an opt-in local script and results must state hardware/runtime, cold load vs inference, dataset size and errors. Sudo authentication requires a real terminal. No live destructive tests on a user's machine.

Architecture: domain contracts/policy ← infrastructure adapters ← application service ← CLI/TUI. Domain has no I/O. See ADR 0001 and SECURITY.md. Public GitHub Actions is used for this independent public repo; no private Nexora CI credentials or production endpoints are imported. The sector profile is locally schema/path validated; the retired OwlSpace map engine is not installed or claimed as validated.

Release: semver tags, annotated notes, reproducible `uv.lock`, wheel/sdist and checksums. `update` checks fixed GitHub upstream; `--apply` requires terminal confirmation and installs an explicit release tag with uv. No automatic installer shell execution.
