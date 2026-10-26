# Changelog

## 0.4.0 — Status treemap, actual-path Clean and the learned cleanup adapter

First public release of the 0.4.0 line; the dev entries below record how it was built.

- **Interactive Status treemap.** Apple's storage category labels as nested proportional maps with mouse/keyboard drilldown. Recorded native totals stay separate from estimated path allocations. A selects known approved actual Trash paths; D reviews them with the existing manifests and No-default consent.
- **Resource-first Clean.** One model judgment per measured resource with native parallel measurement; Clean lists actual file/directory paths only. Owner-tool cache operations are technical advisories and never inflate proposed file bytes.
- **Learned cleanup adapter v3** (`jev-cleanup-laya-runtime-observations-v3`). Published at [ChengyiX/jev-clean-cleanup-adapter](https://huggingface.co/ChengyiX/jev-clean-cleanup-adapter) and pinned by revision and SHA-256. jev-clean downloads it automatically into a private 0600 file, verifies the checksum, then atomically installs it; a tampered installed adapter is refused, and a failed download stops the operation with no fallback. `install.py --adapter` is removed.
- **Plan export survives live caches.** A resource that changes after the scan becomes unselectable with a rescan issue instead of discarding the whole report and plan. Selection, confirmation and apply still fail closed.
- **Model evidence.** Frozen 38-observation native control 34 → 38/38 and authored 120-case regression 114 → 120/120, both with zero false removals; six-order final diagnostic 718/720 with **one false removal**. These are authored controls, not a deletion-safety guarantee — review every proposal.
- **Upgrading.** `jev-clean update --apply` installs 0.4.0 and provisions the adapter during its model-readiness check. The first install or operation downloads about 1.15 GB (base checkpoint and adapter).
- Verification is local (`scripts/verify.sh`); the hosted GitHub Actions workflow is removed.

## 0.4.0.dev5 — Interactive Status treemap (local preview)

### Post-training update — v3 learned adapter

- Locally post-trained the existing Laya encoder-tail/head on observation-shaped counterfactuals from the unchanged v8 production formatter. No scanner, evidence, prompt, ensemble, selection or execution implementation changed; only the learned adapter ID/SHA pins changed.
- Accepted adapter `jev-cleanup-laya-runtime-observations-v3`, SHA256 `5b65d16deeb20ac8c9e6ab43cb3c9fe4478896df8e2326e5744559797546bd33`. The starting adapter is retained and was selectable during development.
- Frozen 38-observation native control: starting34/38, candidate38/38, both zero false removals. Authored120-case native regression: starting114/120, candidate120/120, zero false removals. Six-order final diagnostic718/720 with one false removal; raw error retained.
- Same949 live resource frames: starting0 selectable, candidate32/disjoint declared-cache paths/38.435GB allocated. Full startup94 paths/6.254GB allocated with44 explicit measurement gaps; independent declaration inventory174 roots,0new in the last round. These are model/coverage comparisons, not exclusive reclaim or deletion-safety guarantees.
- **319 tests/82.56% coverage**, Ruff/format/mypy/guards, clean wheel/sdist, native readiness, installed source parity and ``doctor --verify-model`` passed. No files moved/pruned, no remote CI or public release. Methods/sources: [POSTTRAINING-PARITY.md](docs/POSTTRAINING-PARITY.md).

- Apple screenshot's exact ten category labels, nested proportional maps, mouse/keyboard drilldown and one-level back navigation; keyboard list keeps unknown/tiny items reachable.
- Retain actual-path Laya recommendations in Status. Green recommendations, amber selected paths; A selects known approved Trash paths only, Space toggles, D reviews with unchanged manifests and No-default final consent.
- Separate recorded native category totals from estimated path allocations. No invented per-file Apple membership, stale-parent double counting or all-System-Data fallback; typed hierarchy shared with JSON.
- Keep the dev4 actual-path Clean workflow. The post-training update above changes only learned-model provenance; no user cleanup or public release is implied. Research/license/limitations in docs/STATUS-TREEMAP.md.

## 0.4.0.dev4 — Restore actual-file cleanup findings

- Correct command-only regression: Clean lists actual file/directory paths only. Owner actions remain technical advisories and store totals cannot inflate proposed file bytes.
- Restore verified canonical macOS cache/log namespace purpose and descriptive structural facts as learned-model evidence, not disposal permission. Explore nonempty sandbox cache subtrees without dropping opaque account-state siblings.
- Retrain native Laya encoder/head on exact file-resource records; fix evaluation deduplication that had removed sensitive controls from heldouts. Failed runs retained, no perfect-safety claim.
- Candidate read-only benchmark181resources50actualpaths914.9MBallocation31.473s, no personal proposals. Independent60/84control grids0unsupported removes. No files cleaned, no public release assumed.

## 0.4.0.dev3 — Locally trained Laya encoder/head preview

- Actually adapt four native Laya encoder layers and decision head/scorer; pin learned FP16 artifact by checksum. No silent base-model fallback. Batched option-permutation ensemble reduces label-order bias.
- Replace arbitrary path-label cleanup inputs with bounded typed structural/activity facts. Renaming or injected names cannot change classifier state. Unknown facts remain unknown.
- Remove cache-tag disposal admission: tags are observations only, model decides keep/review/remove. Human selection, exact identities/manifests and technical execution checks remain.
- Assess verified installed owner cache operations first (uv/pnpm prune, npm verification, pip purge, Go build-cache cleanup); native pruning is distinct from reversible Trash. Explicit irreversible dialog or CLI CLEAN confirmation, fresh tool/path/activity/model checks, no force flags/arbitrary commands.
- Measured candidate: fresh label-free authored24set22/24correct,0false removals,6/8cleanup positives. Live6roots161resources15.390s,0personal proposals,two native owner opportunities(~3.06GBallocation upper bound). No cleanup/safety guarantee or public release.
- Deep sources, failed runs and limitations are preserved in DEEPER-LAYA-RESEARCH.md; diagnostics never hide raw classifier errors.

## 0.4.0.dev2 — Repair unsupported personal-folder removal proposals

- Require independently observed valid CACHEDIR.TAG cache declarations in addition to model approval; raw remove alone no longer authorizes personal/mixed/unknown data. No folder-name blacklist.
- Revalidate live marker/header/scope at preparation, apply and staging; reject forged/missing/changed plans and declarations. Preserve raw model mistakes in JSON.
- Keep resource speed, simple checkboxes and existing undo. Current cleanup coverage is narrower: untagged app caches/logs/downloads need future verified owner contracts.
- Real synthetic evaluation: 10/20 raw unsupported removes, 0/20 selectable; 4/4 declared cache controls selectable. Live six-root/163-resource read-only check 18.494s, no personal proposals selectable, 12 cache proposals / 7.746 GB allocated. No cleanup or safety-guarantee claim.

## 0.4.0.dev1 — Checkbox-only Clean results

- Show only selectable cleanup items with `[ ]` / `[x]`; remove `?` and `!` rows.
- Remove investigation/unavailable counts, scan-gap banners and inference counters from the Clean results summary.
- Keep model decisions, coverage and errors in the JSON report. No change to model judgments, eligibility, confirmation or execution checks.

## 0.4.0.dev0 — Local resource-first preview

- Replace default per-file neural scanning with disjoint resource discovery, four native measurement workers and mandatory model judgments per resource. No child-file AI coverage claim.
- Show largest-first findings, proposed versus selected bytes, resource counters and explicit incomplete measurements.
- Preserve enclosing resource context for deep paths; use a new exact-input cache namespace.
- Seal selected directory membership before final human confirmation/export; stage whole resources to journaled Trash, revalidate membership and use atomic no-overwrite directory undo.
- Keep both modes, no root deletion or permanent cleanup. Native reads have per-resource deadlines; selected resources may cost extra metadata work. Laya accuracy remains unvalidated.
- Benchmarks: eight explicit roots/175 resources in 20.391s; warm startup scope/2,020 resources in 90.092s with 36 measurement gaps. Not a cold/full-access or reclaimed-space claim.

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
