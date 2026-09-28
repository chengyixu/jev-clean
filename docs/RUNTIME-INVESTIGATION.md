# Runtime regression investigation — 0.1.2

Date: 2026-09-28. Read-only investigation; no user cleanup or unrelated account workflows.

## Reproduced causes

1. Clean asked the decision encoder `inspect/skip` on four broad roots **before collecting their sizes**. A real default run returned four skips, zero discovered children and zero assessed files. The UI's unconditional “Nothing to clean” was false reassurance, not evidence that the disk was clean.
2. Status inspected HOME, attempted a full recursive `du -s` with an eight-second timeout, then spent the entire 200-call model budget classifying the first 200 immediate entries before descending. The root stayed unknown and unvisited other roots remained unknown. Measured children were obscured by the ancestor-only UI frontier.
3. `native.run` discarded `TimeoutExpired.output/stderr`; `measure` only requested a final root sum, so time-limited work yielded no usable progress. macOS permission errors made entire measurements partial even when readable subtrees had useful sizes. Partial output needs preservation, correct lower-bound labeling and no parent/child double counting.
4. Sudo gathered separate native root diagnostics, but these measurements were not consumed by exploration. Elevation therefore did not resolve the discovery problem. Sudo also cannot bypass TCC or authorize root file deletion.
5. The 317.23 GB value was traced to actual native `StorageManagementService` records (byte values that round to that decimal amount), not a literal in application code. The display omitted its recorded timestamp/source; historical log values must not appear as instantaneous authoritative disk state. Private logs/paths are not published here.

A read-only metadata inventory independently found policy-eligible files on the affected machine. That was diagnostic evidence that zero assessed files was a discovery failure, **not** authorization to remove those files. No model approval or deletion is inferred from that inventory.

## Corrective design

- Collect a bounded native inventory first; observations are not cleanup decisions. Use directory-level output so completed subtrees survive timeouts. Retain partial bytes and explicit errors; known children are not hidden by unknown ancestors.
- Let the mandatory model prioritize concrete observed directory choices and assess candidate files. Do not let a binary skip of vague root names pretend to satisfy the user's investigation request. Reserve inference for selected paths and actionable file assessment rather than every immediate entry.
- Give broad directories useful measured subscopes, expose scan budgets and separate observed/protected/model-kept/approved counts. Empty results state their reason and scope, never “disk is clean.”
- Keep filesystem safety vetoes and confirmation unchanged. Preserve the minimal UI. Add left/right button focus, and source/time to the native System Data reading plus full JSON provenance.

## Sources

- Python standard library documentation: https://docs.python.org/3/library/subprocess.html#subprocess.TimeoutExpired — captured output/stderr remain available as bytes on timeout.
- Installed macOS `du(1)` manual: `-d` controls output depth, `-s` emits only a root summary, `-k` uses 1024-byte blocks, `-x` stays on filesystem, `-P` does not follow symlinks (default).
- Apple: https://support.apple.com/en-us/102624 — System Data is the remainder outside more specific categories, not a removable directory.
- Primary model evidence/limitations: [RESEARCH.md](RESEARCH.md), including the out-of-domain weakness of typed-decision checkpoints. A model's choice is not a measurement or a deletion-safety guarantee.

## Privacy and limitations

Private before/after reports remain under ignored `.private/`. Native totals are source- and timestamp-labeled; we cannot reconstruct the exact screenshot event from a matching rounded value alone. Live scans are not atomic snapshots and root permission gaps remain explicit. The comparison with Mole does not justify deleting fresh caches, databases, root files or unassessed content.
