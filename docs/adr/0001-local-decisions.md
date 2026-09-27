# ADR 0001: Mandatory local model, two model-driven workflows

Accepted and revised 2026-09-27. Product: **jev-clean**, a Nexora project; not affiliated with TypeSafe AI. Current product authority: [PRODUCT.md](../PRODUCT.md). Research: [RESEARCH.md](../RESEARCH.md).

Python 3.12+ / Textual provides a keyboard-first TUI and a headless test driver. Both CLI/skill and TUI depend on the same application engine. Domain contracts represent evidence, model decisions and deterministic vetoes. Infrastructure owns native processes, bounded no-follow inspection, pinned Laya-MLX and journaled user Trash.

## Decision

Laya-MLX is a **required dependency and decision engine**. Missing weights or failed inference stop the workflow before producing actionable findings. There is no model-off mode or rules-only fallback. It selects which directories to expand, classifies measured locations, and decides removal disposition for discovered files. Fixed tools provide data and enforce bounded resource use; they do not decide which files are trash. The user may narrow the read scope but cannot expand the removal scope.

Two main modes only: **Clean** (model finds potential trash, user selects and confirms) and **Status** (model determines deeper disk-usage investigation). Administrative commands support setup, updates, reports, history and recovery. The earlier four-mode/optional-model sketch was rejected by the owner and is not the product contract.

Removal decisions use bounded English metadata. Discovery additionally uses short local folder-label hints (untrusted input), never contents or executable commands. The local encoder returns typed choices/probability distributions, not generated reasoning. Explanations display actual evidence and choices, without fabricated chain-of-thought. A `remove` argmax is a proposal, not calibrated safety confidence. A separate hard guard can veto a proposal; it cannot recommend deletion by itself.

Every selected candidate must have model approval and hard-guard approval, then explicit human confirmation. Before staging, the model re-assesses the selection and file identity/open handles are revalidated. Staging is file-only user Trash, with journal and no-overwrite undo. Never empty Trash or delete as root. Root diagnostics are a short fixed native-command allowlist, authenticated in the user's terminal; inference/install/update remain unprivileged.

Demo uses synthetic metadata with **real mandatory inference**. Test-only neural doubles exist at the external adapter boundary; no production switch exposes them. Tests cover missing models, exploration choice effects, malformed outputs, forged plans, symlink/identity races, active files, confirmation/cancellation and recovery. A small real-model evaluation is published as engineering evidence, not as a representative deletion-safety benchmark.

## Accounting integrity

System Data is a native residual, not a folder. Timestamp groups must remain consistent; partial metadata cannot become zero. Filesystem measurements remain unattributed to Apple categories without proof. Nested rows overlap, APFS allocation does not equal exclusive reclaim, and Trash staging does not free space. Unknown attribution is a result, not a reason to hallucinate precision.
