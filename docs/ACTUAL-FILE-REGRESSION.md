# Actual-file cleanup regression and local repair — 2026-10-10

The user asked why Clean only displayed three commands instead of real files.
This was a product regression, not proof that only three cleanup opportunities
existed. Installed dev3 had no generic file remove decisions in live validation:
its evidence described almost every directory as unknown while owner-native
commands had richer documented facts. Command-store allocation (~4.18GB) was
misleadingly added to a proposed total even though pruning would remove an
unknown subset. Commands are not actual file findings.

## Source change / current preview

Verified and locally installed preview version0.4.0.dev4; no public release. Clean only shows learned-model-approved
`trash` file/directory **paths**, largest-first, `[ ]`/`[x]`, one size column.
Owner-native operations are retained as private technical advisories and must
not appear as file checkboxes, be selected with A, or contribute to proposed
file counts/bytes/System Data candidate totals. No extra UI panel is added.

The actual model input now receives typed, independently observed OS storage
purpose: canonical macOS Library/Caches vs Library/Logs vs unverified namespaces.
Apple's filesystem guidance describes Caches for app support data that can be
re-created. This is INPUT evidence, not a rule approving removal; active and
mixed/ambiguous resources can still be kept/deferred by Laya. Arbitrary leaf
names or path text remain excluded; `Pictures/Library/Caches/...` cannot pose as
the canonical cache namespace. Application Support is not labeled cache from
a substring. No invented owner confirmation or absent-uniqueness proof.

Structural format facts describe media/photo libraries, credentials/recovery,
source/repositories, databases, models and disk images without claiming that
extensions prove original/unique/disposable contents. Metadata samples never
establish whole-subtree purity. Cache owners can misuse their storage locations;
rebuildable cache is not necessarily unwanted or zero-cost. Model/human review
and exact metadata manifests remain load-bearing safeguards.

## Actual training progression and failures (retained)

- Concise verified-cache evidence could produce useful raw remove answers, but
  the full scanner record still deferred. Prompt wording alone was unreliable.
- A large replay training run timed out after1200s before producing its final
  artifact. Installed app/model was not replaced by incomplete weights.
- Bounded exact-record native Laya four-encoder-layer/head fine-tunes completed.
  First synthetic heldout looked perfect but independent cache-sensitive tests
  exposed multiple unsupported remove answers. These candidates were rejected.
- Found an evaluation bug: cross-split deduplication silently removed identical
  sensitive cases from dev/final. Regression `test_file_corpus_integrity.py` was
  observed RED. Fixed within-split deduplication and distinct observations so
  every split retains personal/mixed/cache-sensitive scenarios. Earlier perfect
  scores are NOT evidence of safety; the bug is disclosed here.
- Corrected corpus135train/63dev/81final; balanced microbatch2,1200updates,all6option
  orders. Native original Laya final4encoder layers/head/scorer trained. Selected
  on development only, update540/seed10. **Final486layout decisions:484correct,
  0false-removes,52/54 authored idle-cache positive decisions.** Template/format
  heldout is not independent real-world deletion safety validation.
- Independent54-case role/extension/activity controls: only the ordinary idle
  cache-positive was proposed; personal, unknown-use, active, source/media/key/
  vault/database/disk-format controls were not raw remove. Actual Pictures,
  Documents,Desktop,Downloads,Application Support probes kept or deferred.

Learned FP16 artifact150,562,387bytes, id`jev-cleanup-laya-file-resources-v2`,
SHA256`5200fad503588937a20cb78094c8c8731ef35dc8f2ce9c973b860c33c9719a38`.
Base remains pinned native Laya-MLX; no provider/model family switch or hosted
training. Artifact stays private; installer checks exact SHA and real inference.
No population probability calibration or universal safety guarantee claimed.

## Read-only live measurements

Before installing candidate, bounded real app cache/root probe:
**181resources,50actual file/directory candidates,914,874,368allocated bytes,
31.473s**,0measurement gaps,0Pictures/Documentsselectable targets. Three proposal
paths>=100MB,four10–100MB,43smaller. These are learned suggestions, not independently
verified garbage or exclusive reclaim. No files moved. Some caches already empty
or recently cleaned by the user's Mole run; earlier screenshots cannot establish
current recoverable targets. No Mole deletion/source algorithms copied here.

The broad app-cache list is restored, but this does not implement all Mole
categories (old device-support versions, browser-specific incomplete downloads,
application leftovers, project artifact ownership and regenerability still need
separate observation contracts/model validation). Unsupported user/system data
must not be labeled garbage merely to increase the candidate count.

## Regression verification scope

RED-first tests: commands excluded from checklist/bytes/select-all; canonical
namespace evidence only; descriptive format facts; sensitive corpus cases retained;
invalid process text handled; selected recheck preserves semantic purpose and
rejects forged namespace facts. Temporary manifest/staging/restore tests retain
identity/no-follow/ownership/confirmation/undo constraints. Final280tests/80.63%coverage lint/types/guards pass locally and from fresh source
archive/lockedPython3.12; isolated and actual installer verifies exact learned SHA,
real inference and complete installed Python source parity. Actual installed
cache/log/Pictures/Documents scope185resources50actualpaths920,993,792bytes26.137s,
0gaps/0personal proposals/0command rows. Actual installed UI verified3columns and
one size per actual path, select-all excludes advisories. Two largest cache paths
manifest/model-rechecked read-only. Sandbox1530resources32additionalpaths2.15MB
in28.962s,0gaps. These are custom scopes, not whole-disk/exclusive reclaim promises.
No actual user cleanup, monitors, delegation, remoteCI or public release. Existing
sessionPID13497 was not killed/restarted; new model stored separately.

## Sources

- Apple [File System Programming Guide, Library directory contents](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/FileSystemOverview/FileSystemOverview.html), primary OS namespace purpose; no per-file guarantee.
- Native laya-mlx0.2.0 model/runtime and pinned checkpoint, same architecture
  as earlier DEEPER-LAYA-RESEARCH.md; only learned adapter changed.
- Previous raw-model/owner-operation work and its limitations remain in
  DEEPER-LAYA-RESEARCH.md. This repair does not excuse the command-only result.
