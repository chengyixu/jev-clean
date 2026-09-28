# Changelog

## 0.2.0 — 2026-09-28

- Default Clean and Status to whole accessible startup-container filesystem scope, not a cache-root sample. Remove default directory/file/total-duration caps.
- Assess every observed regular file with the model before safety vetoes, including protected and zero-byte files.
- Stream metadata with no-follow directory descriptors; support fixed native elevated find/stat reads; handle APFS snapshot/firmlink aliases and explicit mount/permission gaps.
- Add private exact-input decision caching and restart checkpoints. Show observed/assessed/fresh/reused/approved separately; no pretending cached assignments are new inference.
- Report observed allocated-byte shares and complete-versus-finished coverage separately. First full passes can take a long time.
- Keep existing user confirmation, limited mutation scope, identity/open-handle checks, Trash recovery and automatic model-ready installation.
- Verification distinguishes a complete 7,008,034-file traversal-only check from an interrupted 746,119-file real-model pass; no full neural-pass completion claim.

## 0.1.3 — 2026-09-28

- Fix real discovery failures: model-prioritized concrete locations replace vague-root skip-all; file inference is no longer exhausted classifying every immediate directory entry.
- Preserve timed-out native output, independently measure slow HOME children, consume elevated root measurements, retain partial sizes and expose usable children under incomplete ancestors.
- Replace misleading “Nothing to clean” with observed/assessed/approved/protected or unavailable/incomplete outcomes.
- Label native System Data totals with source/time; S shows exact bytes and provenance. No hardcoded live total.
- Add left/right focus to sudo and deletion Yes/No questions.
- Keep the accepted minimal UI, mandatory model, per-file safety vetoes and human confirmation. No actual cleanup occurred during verification.

## 0.1.2 — 2026-09-28

- Replace the dashboard with a plain two-choice terminal menu.
- Clean: sudo Yes/No → agent logs → file selection → deletion Yes/No. Both questions default to No; existing model/identity/Trash safeguards remain.
- Status: agent logs → locations with usage bars and percentages. Percentages use complete measured rows at one level, never nested parent/child sums; unknowns remain `?`.
- Remove permanent banners, captions, footer, progress panels, debug tables and B toggle. Details/utilities stay on demand.
- Fix literal checkbox rendering and keep percentage columns visible at small terminal widths.
- Refresh actual real-model TUI demo assets. Automatic model-ready installation remains included.

## 0.1.1 — 2026-09-27

- Make **Clean mysterious macOS System Data** the primary Clean workflow and product headline, not a Status-only feature.
- Persistent System Data context in Clean, in-mode investigation/review toggle (`B`), and shared `system_data` JSON evidence for agents.
- Turnkey installer provisions the app, pinned model, checksum validation and real inference before reporting ready; no separate setup command.
- Advanced direct installs automatically provision a missing checkpoint on first operation. Confirmed updates verify the new installation's model.
- Remove the obsolete manual `model setup` command. Integrity/network/inference errors stop readiness without fallback.
- Add installation cold-cache/failure, checksum and Clean-context tests; refresh real-inference TUI demo assets.

## 0.1.0 — 2026-09-27

Initial alpha release, Nexora family.

- Two model-driven modes: Clean and Status.
- Mandatory pinned local Laya-MLX for directory exploration, storage classification and cleanup disposition; no model-free fallback.
- Real decision traces, distributions and inference timing in a keyboard-first Textual TUI.
- Native sudo read-only grounding; timestamp-grouped macOS Storage residual accounting with explicit attribution/coverage limits.
- Explicit all/partial approved-file selection, confirmation, model re-assessment, filesystem vetoes, private journaled Trash staging and no-overwrite restore.
- Shared JSON API and agent skill; private expiring review plans.
- Release checks and explicit confirmed updates; bash/zsh/fish completion, help, doctor and history.
- Synthetic-metadata demo with real model inference; published small diagnostic evaluation including errors and limitations.

Alpha limitations: Apple Silicon only for the model; no promise of complete disk exploration, exact per-file Apple Storage category membership, or safe model judgment. Root cleanup, app uninstall, VM/model/database deletion and automatic Trash emptying are intentionally unsupported.
