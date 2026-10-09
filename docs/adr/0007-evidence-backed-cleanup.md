# ADR 0007 — Model output cannot establish disposability

Status: local 0.4.0.dev2 repair verified and installed; no public release.
Supersedes the **authorization** part of ADRs 0005/0006. Resource-first measurement,
mandatory Laya, checkbox-only review, human confirmation and undo remain.

## Failure and responsibility

A user found Pictures and other personal storage in the cleanup list. A current
read-only Pictures check returned review, so that exact earlier answer has NOT been
reproduced. The broader mechanism IS reproduced: synthetic Documents, Desktop,
Downloads and projects with unknown references/regenerability returned remove.
The model-only pipeline allowed these answers to become ordinary selectable rows.

Grouping made the pipeline faster but increased the consequence of a wrong answer.
Removing diagnostic symbols made the UI simpler but did not repair authorization.
Treating user acceptance of Laya limitations as permission to continue presenting
unsupported whole-folder deletion targets was a design mistake.

## Decision

- A valid model remove remains a **raw classifier answer**, not permission or proof.
  Keep it and all probabilities in the audit. Never rewrite an incorrect answer to
  keep, hide it from evaluation, or describe withheld targets as classified correctly.
- Selection requires both mandatory model approval AND an independently observed
  disposal declaration. The initial source is the published [CACHEDIR.TAG
  specification](https://bford.info/cachedir/), not a folder-name or extension rule.
  Untagged personal/mixed/unknown storage is not selectable even if Laya says remove.
  A directory named cache gets no exception. Renaming data cannot create evidence.
- `DisposalEvidence` records kind, exact covered cache scope and digest of the marker
  identity/header. Directory/file input exposes the observed declaration (or none).
  Candidate.selectable and the shared policy enforce the same evidence contract.
- The observed marker must be a current-user, singly-linked ordinary file, not a
  symlink/special entry or writable by other users. Read only the specified first
  **43 bytes**, validate the exact case-sensitive signature, and bind file identity.
  Ancestor declarations apply only to descendants in the same declared cache tree;
  HOME-level declarations and the marker file itself cannot authorize cleanup.
  Discovery never writes markers or invents certificates for application folders.
- Saved plans are untrusted claims: fresh filesystem evidence must match at selected
  preparation, apply and immediately before staging. Missing, forged, removed or
  changed markers fail closed. Existing fingerprints/manifests, owner/path checks,
  explicit selection, confirmation and transactional no-overwrite undo remain.
- Old broad plans cannot pass new runtime checks. The input/cache contract changes
  so previous model-only decisions are not mistaken for new evidence observations.
- Recovery does not need disposal evidence: new admission rules must not strand
  previously staged user data or break legacy file journals.

## Limits and usefulness

CACHEDIR.TAG describes a cache owner's declaration of regenerable data. Its primary
purpose is excluding caches from backups/copies; the specification does NOT prescribe
an age policy or claim deletion is always appropriate. It is not cryptographic proof
of the generating tool, inspection of contents, zero regeneration cost, or protection
against same-user false declarations. Model and human review still matter. Do not add
a tag to an arbitrary directory to force cleanup.

This intentionally admits fewer resources. Tagged uv/Gradle cache scopes are supported;
other app logs/caches, abandoned downloads, old updates and developer artifacts without
observed owner declarations remain unselectable until a separate verified tool contract
is implemented. No broad Application Support/Downloads/project folder authorization,
confidence threshold, Pictures blacklist or deterministic rules-only mode is introduced.
No native permanent pruning or automatic Trash emptying. Trash staging frees no space.

No hosted provider/model switch or user content upload. The scan still measures all
requested resource boundaries and assesses their evidence, preserving scope, speed and
raw mistakes. This is a correction to **permissions**, not improved Laya accuracy.

## Actual evaluation

`scripts/evaluate_disposal_authorization.py`: 24 temporary synthetic resources with
real pinned Laya; 20 untagged personal/mixed/renamed controls, four tagged cache controls.

- **10/20 untagged controls received raw remove answers.** These remain failures of
  classification, not claimed safe decisions.
- **0/20 unsupported controls became selectable.**
- **4/4 declared cache controls became selectable** with model approval.
- Evaluation took **0.824 seconds** after model load. Small authored engineering
  cases are not population safety calibration or a domain-trained model benchmark.

Read-only live custom scope: six roots (personal locations plus uv/Gradle cache scopes),
163 resources in **18.494 seconds**, zero incomplete native measurements. No selectable
personal proposals; 12 declaration-backed cache proposals totaling **7.746 GB allocated**.
This is not independently inspected garbage, exclusive APFS reclaim or bytes freed.
No user file was moved and no API credentials were exposed. Private reports remain
ignored; only synthetic cases and aggregate verification belong in public docs.

## Installed verification

209 tests, 81.35% coverage plus lint/types/guards passed locally and from a fresh
source archive with locked Python 3.12. Isolated and actual source installations
verified the pinned checkpoint and real inference. Installed Python files matched
source. Actual CLI synthetic controls kept all outside-HOME targets unselectable
and permitted only the declared cache among five in-HOME personal/renamed/cache
controls. No user data moved. No remote CI or public release was performed.

## Regression spine

RED-first tests reproduce untagged remove admission, invalid/symlink/writable markers.
Tests cover renamed controls, positive declarations outside old cache allowlists,
forged plans, wrong scope, removed/changed ancestor declarations, marker exclusion,
checkbox select-all exclusion and legacy recovery. Temporary cache fixtures explicitly
create owner declarations; no production fake evidence flag exists.
