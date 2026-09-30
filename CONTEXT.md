# Project context

Release 0.3.0: model-owned keep/review/remove with no directory/extension/retention classification veto. ADR 0005 records the owner-reviewed, owner-accepted model error rate. Existing installations require an explicit update; check the installed CLI rather than assuming a version.

Release handoff: the owner authorized 0.3.0 with the known model errors disclosed. Publication and installation must be checked against the release URL and CLI, not inferred from this source document. Human review is the load-bearing safeguard. The 24-scenario real-model evaluation has two false removes in structured inputs; a 0.4.0 candidate should consider domain fine-tuning or a stronger local checkpoint rather than widening scope. Resource grouping and authoritative reference/regenerability probes are still absent. No user cleanup was performed.

jev-clean is a standalone Nexora-family macOS tool. Python 3.12+, Textual 1.x; mandatory Laya-MLX 0.2.0 on Apple Silicon macOS 14+. Only Clean and Status are main workflows, both model-driven. Pure/adapter-boundary tests run cross-platform; the application and real-inference demo require Apple Silicon macOS. No backend service, account, or API key is required. Installation includes automatic pinned-model provisioning and real-inference verification. A cold/incomplete cache also provisions automatically on first operation. No manual model setup is required. Network is used only for these provisioning/install paths and release checks.

Whole-disk scope: default mounted startup APFS container, not just user caches. No default scan cap; all observed regular files reach the model before technical execution-readiness checks. Exact-input inference cache and counters are described in docs/WHOLE-DISK.md. Esc stops a pass; restart re-enumerates with cached decisions.

Local runtime data: `~/.local/state/jev-clean/` (private JSON plans/journals and `disk-scan/` decision/checkpoint database), `~/.Trash/jev-clean-<batch>/` (staged files), Hugging Face cache (pinned model weights). These are not project artifacts. `.private/` is ignored for local evidence. Never publish an actual machine audit.

Verify with `scripts/verify.sh`. Hosted CI covers Linux and macOS pure/fixture behavior; actual Apple Silicon model evaluation is an opt-in local script and results must state hardware/runtime, cold load vs inference, dataset size and errors. Sudo authentication requires a real terminal. No live destructive tests on a user's machine.

Architecture: domain contracts/policy ← infrastructure adapters ← application service ← CLI/TUI. Domain has no I/O. See ADR 0001 and SECURITY.md. Public GitHub Actions is used for this independent public repo; no private Nexora CI credentials or production endpoints are imported. The sector profile is locally schema/path validated; the retired OwlSpace map engine is not installed or claimed as validated.

Release: semver tags, annotated notes, reproducible `uv.lock`, wheel/sdist and checksums. `update` checks fixed GitHub upstream; `--apply` requires terminal confirmation and installs an explicit release tag with uv. No automatic installer shell execution.
