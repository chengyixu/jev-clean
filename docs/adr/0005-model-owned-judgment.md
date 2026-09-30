# ADR 0005 — Model owns disposition; execution is not a second classifier

Status: **Accepted for the 0.3.0 alpha release** (2026-09-30). The owner reviewed the
model-evaluation evidence below, including both false-remove cases, and chose to
release with the Laya-MLX backend. The measured accuracy limits are a permanent
part of this decision, not a resolved defect.

Supersedes the classification-veto portion of ADRs 0001–0004. Does not change
whole-disk observation, minimal two-mode UI, mandatory local inference, or human
confirmation. Existing v0.2.0 clients keep their old behavior until explicitly updated.

## Why

The previous release observed the whole disk but only admitted four small roots,
specific log extensions and fixed retention windows for mutation. Millions of
model decisions could not materially affect the result. A tiny approved total
was not a measurement of all disposable data. Inputs omitted application
relationships and conflated unrelated files with identical coarse metadata.

## Decision

- Remove directory allowlists, protected extension/component lists and fixed
  age thresholds from disposition handling. Open handles and hard links are
  facts for the model, not application-level garbage classifiers.
- `recommended` records the model's remove answer independently of `eligible`
  (technical staging readiness). A valid keep/review answer is never selectable.
  A technical failure does not rewrite a remove answer to keep.
- Preserve typed-output validation, current-user-only regular-file staging,
  no-follow path handling, original target fingerprints, operation permissions,
  transaction-state integrity, explicit selected IDs/confirmation and undo.
  These cannot invent a remove judgment. No recursive or root deletion.
- Refresh metadata, activity and application observations before mandatory
  re-inference. A changed target identity requires another scan/review. A changed
  activity observation at the rename boundary also requires reassessment.
- Include bounded local directory labels, extension, actual link/activity facts,
  and installed application ID/version observations from bounded Info.plist reads.
  Identifier equality is only a naming relationship, not proof of ownership.
  Runtime references, regenerability and obsolescence remain explicitly unknown
  unless actually observed. No resource contents, basenames or remote inference.
- Cache complete serialized input, questions, label mapping, input contract and
  pinned model/runtime identities. The old coarse-input namespace cannot leak
  into this contract. Refuse model inputs that exceed the actual token budget,
  rather than allowing silent truncation.
- Keep model `review` rows visible as `?`, unsupported removal rows as `!`, and
  selectable removal rows as checkboxes. No new mode/dashboard. `review` means
  evidence is still needed, not that an autonomous dependency investigation was
  completed. Resource grouping and application-native dependency probes remain
  unimplemented; directory manifests alone do not establish disposability.

## Model evidence: known, accepted limitation

Real inference, pinned `aac6fef/laya-mlx` revision
`20aed815fc6acde75733882e7ec0e3f28aeb9717`, runtime 0.2.0, Apple Silicon:

1. An initial expanded rubric answered **5/12**, selecting keep for every case.
2. The old v0.2.0 rubric answered **10/12** on those plain-evidence cases but
   incorrectly selected removal of a required current VM containing unique work.
3. Neutral choice labels A/B/C answered **10/12** on that development set; this
   motivated the current bijective label mapping, not a confidence cutoff.
4. The frozen current prompt was tested through both plain and application-style
   structured inputs, plus 12 additional scenarios written after selection:

| Set | Representation | Exact | False remove | Missed remove |
| --- | --- | ---: | ---: | ---: |
| Development (12) | Plain | 10/12 | 0 | 2 |
| Development (12) | Structured | 7/12 | 1 | 2 |
| Post-selection (12) | Plain | 11/12 | 1 | 0 |
| Post-selection (12) | Structured | 9/12 | 1 | 1 |

Structured input incorrectly recommended removing the only backup private key.
Both representations incorrectly recommended removing unavailable-to-redownload
weights required for offline work. **These are known, published,
owner-accepted incorrect-remove answers, not hidden by filesystem-type vetoes in
these measurements.** Human review of every proposed file is therefore the
load-bearing safeguard for this release, and a 0.4.0 candidate should consider
domain fine-tuning or a stronger local checkpoint rather than widening scope.

Run `scripts/evaluate_model_authority.py --output <private-path>` with the real
model to reproduce. Cases are synthetic, small, authored by the developer and
not a representative benchmark. Development cases informed prompt selection;
post-selection cases are not a statistically independent population sample.
Production collectors cannot yet obtain every natural-language fact supplied
by these fixtures. No safety/accuracy claim follows from zero errors in any
subset. The upstream confidence-clamping warning applies to its 11+ choice
bucket, not specifically this three-option question; it does not validate our
three-option calibration either.

The local model is Laya, **not official TypeSafe Jev**. Official Jev was not
called or evaluated and no API credential or user metadata was sent remotely.
No model-quality conclusion here should be attributed to Jev. A better local
checkpoint/domain training or a separately authorized official-API integration
remain future options. Human confirmation is retained as the primary safeguard
and is not a licence to hide the errors above.

## Primary sources consulted

- [Laya model card](https://huggingface.co/convaiinnovations/laya): retrieved for
  this investigation. Its Honest Limits section reports near-chance zero-shot
  typed decisions for base checkpoints, overconfidence, and label sensitivity.
  Fine-tuned results belong to a different checkpoint/task distribution.
- [Pinned MLX model](https://huggingface.co/aac6fef/laya-mlx) and installed
  `laya_mlx.common.build_sequence` / `Agent.prepare`: verified the combined
  context limit and silent truncation behavior before adding a rejection check.
- [TypeSafe introduction](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
  and [documentation](https://docs.typesafe.ai): typed state/question interface,
  not an autonomous filesystem observer. Live documentation retrieval was
  intermittent; no official Jev parity or measured accuracy claim is made.
