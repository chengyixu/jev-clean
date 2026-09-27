# Verification record

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
