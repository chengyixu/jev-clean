# Changelog

## 0.3.0 — 2026-09-30

**Breaking change: the model alone decides keep/review/remove.** The previous
four-root, extension-list and fixed-retention mutation policy is removed. This is
the accepted consequence of [ADR 0005](docs/adr/0005-model-owned-judgment.md).

- Delete directory allowlists, protected extension/component lists and 14/30-day
  retention gates. Code no longer classifies a path, extension, age, open handle
  or hard-link count as trash or as worth keeping.
- `recommended` now records exactly what the model decided; `eligible` records
  only whether the executor can stage that exact target. A mechanical refusal no
  longer rewrites a remove answer into a keep.
- Enrich model evidence with bounded local directory labels, file extension,
  measured filesystem facts and installed application identifier/version read
  from bounded `Info.plist` metadata. Reference, regenerability and obsolescence
  stay explicitly `unknown` until actually measured. No resource contents or
  basenames enter inference.
- Refresh metadata, activity and manifest observations before mandatory
  re-inference when a plan is applied; refuse a changed target identity and
  refuse a changed activity observation at the rename boundary.
- Key the decision cache by the full input, question, label mapping, input
  contract and pinned runtime so legacy coarse-input decisions cannot be reused.
  Reject model inputs that exceed the real token budget instead of silently
  truncating evidence.
- Use neutral A/B/C choice labels and translate them to dispositions, after
  measuring that descriptive labels biased the checkpoint toward one answer.
- Show `?` for model review and `!` for removal proposals the executor cannot
  stage, next to selectable removals. Same two modes, same minimal UI.
- Known model failures retained and published: 24 synthetic scenarios
  answered 16/24 with structured application-style input, including two
  incorrect-remove answers (unique private key, required offline model weights).
  The owner reviewed and accepted this risk. Human review of every file is the
  load-bearing safeguard; no rule hides the errors.
- No hosted model, no metadata upload, no official Jev API call and no
  credentials. Installed weights and runtime remain pinned as before.

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
