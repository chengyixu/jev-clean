# Nexora Research: post-training with a frozen cleanup interface

Authors: Chengyi Xu and Nexora

This work investigates learned cleanup decisions while keeping the application's scanner, observation schema, prompts, selection rules, execution checks, and UI unchanged. It concerns the existing local Laya adaptation, not official TypeSafe Jev. Actual-machine audit records and candidate weights remain private.

## Why supervised post-training first

The upstream Laya Typed-Decisions card describes task-specific RLCD training with a proper-scoring reward, REINFORCE, and an auxiliary soft cross-entropy objective. It also explicitly cautions that specialization does not establish transfer to unrelated tasks [1]. Cleanup has a small typed action space and authored counterfactual labels; a direct supervised objective provides a reproducible first intervention. An interactive reward or trustworthy preference dataset is not available here. Calling cross-entropy training “RL” would be inaccurate.

Typed decision models can prefer option labels over their definitions. The relevant open-model study recommends measuring that failure and reports that confidence thresholds do not reliably catch it [2]. The existing application already uses neutral options and a six-permutation ensemble. This experiment preserves that inference implementation and augments training over the same six option orders. It introduces no confidence gate or path-based override.

A separate Laya reproduction reports disagreement between calibration claims and measured confidence direction, and failed out-of-distribution transfer on its exploratory probe [3]. Those are results for another checkpoint and dataset, not numbers for this application. They reinforce the need to measure the actual deployed ensemble and to keep “model probability” separate from “deletion safety.”

## Frozen production boundary

Only model artifact identity and checksum metadata may change when an accepted adaptation is installed. Production measurement, resource discovery, factual evidence, `observed_state`, question definitions, probability averaging, eligibility, manifests, staging, and restoration retain their existing implementations. Training and evaluation helpers live under `scripts/` and `tests/`; they are not imported into the application's runtime decision path.

The training corpus calls the existing production observation formatter. It adds no Xcode namespace, inferred owner statement, additional file-content observation, folder blacklist, filename-based disposal rule, or synthetic fact to real scans. Private experiments that depended on an expanded observation interface are excluded from this implementation.

Existing custom-root and Status drill-down operations can expose a smaller resource for another measurement and model judgment. Post-training cannot reveal descendants that were never presented to the model. Nor can training reliably distinguish two resources whose complete model inputs are identical but whose actual retention needs differ. Such cases remain a limitation of the frozen information boundary.

## Data and controls

`scripts/runtime_resource_corpus.py` extends the existing authored file-resource corpus using only current observations:

- Observed valid cache-owner declaration versus no declaration.
- Idle, currently active, and unknown activity for otherwise matched observations.
- Source, media, credential, model/disk-image, and database formats within declared resources.
- Different entry counts, suffix combinations, and directory layouts across train, development, and final splits.

No actual user paths or resource contents are training inputs. A declaration is evidence of regenerability, not proof that every application uses it correctly or that the owner has no retention requirement. Removal labels request a human-review proposal under the existing alpha contract; they do not certify safe irreversible deletion.

Corpus checks reject contradictory labels for identical observations, cross-split semantic-family overlap, and exact-text leakage. Sensitive controls remain represented in every split. New native holdout observations are frozen before candidate evaluation. Behavioral counterfactuals supplement aggregate accuracy, following the motivation of CheckList [4]. Authored controls are not independent human ground truth.

## Reproducible experiment

Generate a corpus with `python scripts/runtime_resource_corpus.py --output <private-corpus.json>`. The existing encoder-tail trainer accepts that frozen JSON through `--corpus`. It retains its existing architecture, native question construction, prefix/tail equivalence checks, option-target remapping, bounded optimizer settings, and development-only checkpoint selection.

The starting adapter is now an eligible checkpoint at step zero. If optimization introduces regressions, the research harness can retain that original checkpoint instead of being forced to select a trained regression. `--native-development` selects checkpoints by calling the application's existing six-order probability ensemble directly; raw single-layout errors remain in the same report. This aligns research selection with the deployed inference unit without changing that unit. These are offline training-selection safeguards, not production decision overrides.

Current experiment design: four existing encoder-tail layers plus the original decision modules; six training option orders; microbatch four; 600 updates; learning rate 0.000003; false-removal training cost four. Counts and observed results must be read from the frozen corpus and retained experiment report rather than inferred from this design description. Device cache limits used by a research process do not modify the application runtime or cap active model memory [5].

## Observed model results

The selected checkpoint was update 300, chosen on the 102-case development set through the unchanged deployed ensemble. Native ensemble scores improved from 96/102 to 102/102 on development and from 114/120 to 120/120 on the authored regression set; both starting and selected models had zero false removals in those native comparisons. A separately frozen 38-case native control set improved from 34/38 to 38/38, with the four declared-idle positives changing from review to remove and zero false removals in either model.

Individual option orders remain imperfect: the selected model's 720-layout final diagnostic scored 718/720 with one false removal and one missed removal. The application continues to average all six existing probability permutations; it does not choose a favorable order. These are authored synthetic observations, not independently reviewed real-file safety measurements. The 120-case set is a regression set after prior experiments; the extra 38 observations were frozen before their first candidate evaluation. Neither result establishes universal cleanup accuracy.

The accepted artifact identity is `jev-cleanup-laya-runtime-observations-v3`, SHA256 `5b65d16deeb20ac8c9e6ab43cb3c9fe4478896df8e2326e5744559797546bd33`. It retains the existing pinned base checkpoint and tensor layout. Only the application's and installer's artifact-provenance literals change; the production observation/prompt/scanning/execution implementations remain byte-identical. The private adapter is required to install this local preview; this document is not a public model download or release announcement.

## Acceptance and limits

Evaluate starting and candidate adapters through the unchanged native six-option ensemble. Report complete confusion matrices, false removals, useful-removal recall, option-order behavior, and readiness-control output. Evaluate held-out controls and repeat live read-only comparisons before changing artifact pins. Preserve failed-candidate reports and raw errors.

Useful extra proposals must not come from relabeling uncertain personal data as disposable. More proposed bytes are not, by themselves, improvement. Conversely, zero approvals do not establish a clean disk. Coverage gaps, unresolved references, large retained resources, allocated-byte upper bounds, and actual freed space remain distinct.

Actual removal still requires human-selected IDs, fresh reassessment, exact selected-directory manifests, and final confirmation. This work neither stages user files nor empties Trash. Native-machine evidence belongs under ignored `.private/` and must not be published as a public machine audit.

## Sources

1. Convai Innovations, [Laya Typed-Decisions model card](https://huggingface.co/convaiinnovations/laya-typed-decisions/blob/5ee0035de4e8db341564dad9e4f24a39b52b7f10/README.md). Primary model-card description of training, specialization, and stated limits; its benchmark claims do not validate cleanup behavior.
2. Azizi et al., [Labels Override Definitions in Jev-Style Typed Decision Models](https://arxiv.org/html/2610.02586). Open-model preprint; option-label bias and mitigation measurements, not an evaluation of the closed Jev service.
3. Nandakishore, [Laya as a Typed Probabilistic Assessor: An Independent Reproduction and a Preregistered Study of Calibration and Selective Escalation](https://arxiv.org/html/2609.33843v1). Preprint; checkpoint-specific reproduction, calibration direction, and transfer limitations.
4. Ribeiro et al., [Beyond Accuracy: Behavioral Testing of NLP Models with CheckList](https://arxiv.org/abs/2005.04118), ACL 2020. Behavioral testing methodology and counterfactual/invariance controls.
5. MLX, [set_cache_limit documentation](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.set_cache_limit.html). Primary API reference: reusable free-memory cache, distinct from active model/optimizer memory.
