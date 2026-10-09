# Laya cleanup learning experiments — 2026-10-09

**Result: real weights were trained, but the model-only replacement failed validation
and was not installed.** Installed CLI remains 0.4.0.dev2 with its existing admission
protection. This experiment does not satisfy the user's desired removal of that
protection. No production prompt, model, provider or user data was changed.

## Request and approach

The user rejected path/tag cleanup rules and requested better Laya decisions.
`/find-skills` found `wdobry/laya-playground`'s laya-integration guidance; it was read,
not installed or executed. It recommends factual/entailment questions rather than
asking an encoder to plan actions. Upstream Laya `docs/finetune.md` and native MLX
model/runtime were read. No other model/account, hosted teacher or provider was used.

Experiments tried factual questions, evidence representations, original Laya scorer
weight training and original Laya decision-head/scorer training. There is no
cache-tag permission gate or confidence threshold in the reported raw metrics.
Training examples are authored synthetic English observations, not personal contents,
external ground truth or a teacher's generated classification.

## Data and boundaries

- Initial family-disjoint splits: **72 training cases / 18 families**, **12 development
  cases / 6 families**, **30 diagnostic test cases / 15 families**. Variants change
  irrelevant age/size/activity metadata without encoding the answer in folder names.
- The first diagnostic test became exposed after scorer evaluation. Subsequent head
  training therefore uses a **new final set of 24 cases/families**, authored and
  frozen before head inference. The earlier test is not described as still untouched.
- Final cases include required offline installers, actively used caches, unique legal
  records/credentials, backups, opaque numeric metadata, stopped images, unknown
  downloads, discarded exports and reproducible generated outputs. Labels include
  remove, review and keep; keep-everything does not count as success.
- These are small, author-selected families with related semantic themes. Family/text
  disjointness prevents direct variant leakage, not population-level independence.
  The final set is NOW exposed. Further development needs another untouched holdout.
- Most synthetic descriptions provide ownership/dependency/uniqueness facts that
  production collectors cannot establish. An improved score on this task would not
  establish correctness over the current scanner's thin metadata.

## Model and training

Base: pinned `aac6fef/laya-mlx` revision
`20aed815fc6acde75733882e7ec0e3f28aeb9717`, laya-mlx 0.2.0, MLX 0.32.2 on Apple
Silicon. The experiment's factual question is saved in the report; the baseline
below is the base checkpoint **with that question/evidence**, not an accuracy claim
for the installed resource prompt. No silent base checkpoint replacement.

1. Scorer only: freeze encoder and decision head, cache native marker features,
   fine-tune existing scorer with cross-entropy, AdamW 1e-4, microbatch 12,
   160 updates for each of seeds 0/1/2. Validate cached logits against native forward.
2. Head + scorer: freeze encoder/type embeddings, cache token embeddings, fine-tune
   the original two-layer decision head and scorer in float32 with cross-entropy,
   AdamW 2e-5, microbatch 4, 160 updates per seed. **26,245,121 parameters** trained;
   30 parameter tensors changed. No new bespoke classifier replaced Laya's readout.
3. Select checkpoints/seed using development false-remove count then accuracy,
   never final-test results. Inspect raw argmax answers and useful-removal recall.
   No probability calibration was performed or claimed. Cross-entropy fine-tuning
   is not upstream RLCD or full-backbone fine-tuning.

## Actual measured results

| Model / set | Correct | False remove | Useful-removal recall |
| --- | ---: | ---: | ---: |
| Base factual question, train | 51/72 | 13 | 91.7% |
| Base factual question, dev | 10/12 | 1 | 100% |
| Base factual question, diagnostic | 27/30 | 1 | 90% |
| Scorer fine-tune, diagnostic (all 3 seeds) | 28/30 | 1 | 90% |
| Dev-selected head+scorer seed 0, diagnostic | 26/30 | 0 | 70% |
| Base factual question, new final | 22/24 | 2 | 100% |
| Head+scorer, new final (all 3 seeds) | 22/24 | 2 | 100% |

The new final failures were **a required offline recovery installer** and **a cache
currently used by an active job**. They remain raw model errors. Seed 0's diagnostic
false-removal improvement came with missed disposable targets and lower overall
accuracy. The other head seeds reached 28/30 on the diagnostic, still one false
remove. None improved final results. Do not cherry-pick the zero diagnostic count.

The dev-selected learned head was reloaded into the native Laya model in an isolated
process, cast to float16 and run through real inference. Its diagnostic/final choices
matched the cached-feature float32 choices exactly (0 mismatches). This validates
that the weight artifact actually operates in Laya; it does not validate its decisions.

The scorer run took about 1–3 seconds of optimizer work per seed after features;
initial head optimizer runs took 16.7–57.0 seconds per seed under machine contention.
A durable seed-0 reproduction took 6.747 seconds and reproduced checkpoint step 140
and all reported counts. Timing varies, excludes feature extraction/model load, and
is not production inference/cleanup performance. Saved adapters are approximately
100 MB for head+scorer and remain in ignored private storage, not installed weights.

## Prompt/evidence probes

Four plausible factual rubrics evaluated on the same 12 development cases produced
**1, 4, 5 and 6 false removes**, respectively. A separate already-exposed 24-case
structured-evidence diagnostic improved total correctness with a factual question
(16/24 versus the installed resource prompt's 11/24), but increased false removes
(2 versus 1). A natural-language unknown-evidence template withheld 20 named negative
controls but missed 3/4 tagged-cache positives. This is exploratory evidence of
representation/label sensitivity, not independent generalization or a deployment gate.
No such prompt was installed.

## Reproduction and verification

Use a private output directory, without root:

```bash
uv run python scripts/laya_cleanup_experiment.py \
  --output .private/laya-cleanup-learning --steps 160 --seeds 0 1 2
uv run python scripts/laya_cleanup_head_experiment.py \
  --output .private/laya-head-learning --steps 160 --seeds 0 1 2
```

The second tool loads `scripts/fixtures/laya_cleanup_head_final.json`, preserving the
original final cases. Both tools lazily import MLX so evaluation-integrity tests are
portable. Tests assert split leakage is rejected, raw false-removes remain counted,
checkpoint selection ignores final scores, final errors prevent deployment, and
keep-everything cannot be claimed an improvement. The last checks are OFFLINE model
admission checks, not per-resource hardcoded classifiers.

Final verification: **217 tests, 81.35% coverage**, Ruff, mypy and repository guards
passed locally and in a fresh source archive/locked Python 3.12 environment. Eight
learning-contract tests cover the split/metric/selection boundaries. The packaged
source includes the synthetic final fixture and lazy-import research tools, not
private trained adapters. Installed dev2 Python source remained unchanged and matched
checkout. No public release or remote CI of this research change.

Private reports/checkpoints remain under `.private/laya-*`; no real file lists,
credentials or user contents are published. No training in the installed runtime,
root process, deletion, monitors, subagents or external GPU service.

## Deployment decision and next work

**Not deployed.** Learned candidates failed the new final test; installed protection
was not removed. Full-checkpoint checksums, runtime loading and installer contracts
are unchanged. This is a failed bounded model-improvement experiment, not a repaired
production model.

Next substantive work is a broader independently reviewed cleanup corpus spanning
real observation shapes and unknown/mixed/active/required data, bounded read-only
application reference/uniqueness observations, and fuller fine-tuning (encoder or
adapters) plus held-out calibration and a new final set. Do not infer recoverability
from names or fabricate facts to satisfy the model. A tiny synthetic set and prompt
rewrites are insufficient justification to hand arbitrary whole-folder disposal to
this checkpoint. Human confirmation is not an excuse for known false-removal errors.
