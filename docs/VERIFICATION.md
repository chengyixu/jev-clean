# Verification record

## 0.1.3 — Live discovery and measurement fixes

- 106 tests pass; coverage 81.04%; lint/types/safety gates pass. New failing-then-passing regressions cover timeout stdout retention, partial subtree parsing, unknown-ancestor masking, wide-directory budget starvation, left/right dialog focus, truthful empty outcomes, source/timestamp display, reader cancellation/reaping and elevated-output consumption.
- Real read-only default Clean, after the fixes: 122,041 nonempty file observations; 412 model assessments; 272 approved review candidates (~60.8 MB). This is a point-in-time run under unchanged safety rules, not a reclaim promise; no files were removed.
- Real read-only default Status: 623 measured nodes and 419 numeric-share rows, instead of four unknown roots. Coverage remains explicitly partial. Slow HOME children no longer suppress all measurements.
- The reported native number was traced to actual StorageManagementService log records that round to the user's value. Exact source/recorded time is now displayed and available via S/JSON; raw private logs remain excluded.
- Authenticated sudo diagnostics were not exercised by the agent because no cached authorization existed; safe failure and elevated-output wiring are covered by boundary tests. No password was requested or recorded.
- All subsequent diagnostics, implementation and verification after the user's restriction ran directly in foreground, without monitors or delegated agents.

## 0.1.2 — Minimal terminal

- 87 tests pass; coverage 80.43%; lint/type/safety gates pass. A real 80x24 PTY run verified startup → Status with actual model inference and percentage rows → clean quit.

- Sequential TUI verified at 80x24 and 60x20: two-choice home, Clean sudo Yes/No, logs-only running stage, approved file selection, default-No delete confirmation, cancellation/error handling, Status usage bars and drill-down.
- No persistent Header/Footer/ProgressBar or dashboard panels. Literal `[x]` checkbox rendering and long-path percentage visibility have regression tests.
- Percentage tests establish 50/30/20 shares for disjoint fixtures without adding children twice; incomplete/unknown rows get no invented percentage.
- Public screenshots/GIF recaptured from the real app with real model inference on synthetic disk metadata. OCR confirms the plain menu, flowing logs, selected file, Yes/No question and percentage rows.
- Mandatory model, file safety, Trash/undo, automatic installation and private JSON evidence remain unchanged. No real user cleanup performed.

## 0.1.1 — System Data Clean and turnkey installation

- 75 tests pass; coverage 80.87%, with Ruff, mypy and architecture/safety gates passing.
- New tests demonstrate automatic cold-checkpoint provisioning, cached no-network preparation, checksum tamper rejection, failed-download/inference readiness failure, exact newly installed executable verification, update readiness checks, and System Data visibility across Clean selection and its investigation toggle.
- A real **isolated installation with empty HF_HOME** succeeded: app/runtime install, pinned model download, file checksums, actual inference, then a real-inference Clean demo with the new System Data context. No separate model-setup command was run. Global tool installation was not replaced.
- The normal CLI no longer exposes `model setup`; advanced direct installs prepare missing weights automatically. `doctor --verify-model` is an installer readiness primitive, not a manual setup prerequisite.
- Refreshed public demo/assets show the actual Clean System Data panel, model decisions and the in-mode investigation view using synthetic data. OCR verified those labels; no private machine data was published.
- Existing deletion/privilege boundaries remain unchanged. No real user cleanup was performed.

## 0.1.0 — Initial alpha baseline

## Local target

- Apple Silicon arm64, macOS 27.0, Python 3.12.12.
- Laya-MLX 0.2.0 and pinned `aac6fef/laya-mlx` revision `20aed815fc6acde75733882e7ec0e3f28aeb9717` loaded successfully; real inference exercised.
- **59 hermetic tests passed** at this checkpoint; coverage **78.62%**, configured CI floor 75%. Tests isolate files under temporary homes and substitute only the external neural adapter where appropriate.
- Ruff lint/format and mypy pass; local architecture/safety guards pass.
- Wheel and source distribution build; archive audit found no `.private`, environment, credential or model-weight files.
- Real read-only macOS Status investigation completed with the model making 13 directory-expansion decisions and reporting 188 nodes. Exploration hit its explicit bound and was correctly labeled incomplete. Native Storage category logs were unavailable in that run; no category attribution was fabricated. The private report is not published.
- Real-inference Clean demo: five synthetic locations explored, five files assessed. The model selected one removal proposal; active/database/unknown cases remained unselectable. This is wiring evidence, not cleanup accuracy proof.
- Actual TUI SVG/PNG exports and GIF screen sequence were rendered with real inference on synthetic metadata. Keyboard navigation/select-all/none/search/confirmation cancellation and terminal resize are covered by headless Textual tests. Pixel output was checked via OCR; no subjective visual-design review is claimed.

## Model evaluation

See [model-evaluation.json](model-evaluation.json) and `scripts/evaluate_model.py`. The 12 hand-authored examples achieved 7/12 exact desired dispositions. Zero protected/uncertain cases passed the combined model-plus-guard selection gate. Do not confuse those two metrics. The prompt was iterated using similar examples, so these are not held-out statistical accuracy estimates. Latency includes synchronized typed inference and formatting, excludes model load, and varies with other machine workloads. Raw samples are retained.

The runtime warned about clamping an upstream `choice:11+` calibration bucket. This application uses two, three or four choices, but the warning is retained rather than suppressed. No domain-specific safety calibration has been performed.

## Deliberate limits

No real user file was removed while developing/testing this release. Destructive-path behavior was exercised on temporary files only. Sudo command allowlisting and failures are tested; actual interactive authenticated deep diagnostics were not performed by the development agent. Full Disk Access/SIP/TCC gaps remain visible. No external OwlSpace map-engine certification is claimed; the local sector profile passes structural path validation.

See public CI for clean foreign-machine test results and release artifacts for distribution checksums. Additional release checks are recorded in the release notes rather than rewriting historical measurements as if they happened earlier.
