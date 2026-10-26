# Status treemap — research and contract

## Summary

The local dev5 Status client is an independently implemented terminal treemap.
It uses the user's screenshot's exact ten labels, layered click/keyboard navigation,
Laya recommendation colors and human-controlled selection. Clean remains the dev4
actual-path checkbox list. This is not an Apple-equivalent per-file classifier or
a SpaceSniffer port.

## Research findings

1. **Apple category meanings are documented, membership is not exposed by that
   documentation.** Applications excludes built-in system apps; Photos refers to
   the System Photo Library, not every image; iCloud Drive may include Desktop and
   Documents; System Data includes resources not in the named categories. Apple
   explicitly calls out logs, caches, VM/runtime data and app support [1]. Exact
   namespace grouping is therefore an estimate, not a verified Apple assignment.
2. **SpaceSniffer's relevant pattern is progressive disclosure.** Its developer
   describes proportional rectangles, single-click detail and double-click zoom
   [2]. Here a single click opens the next map level; Esc returns one level. A
   list provides the same navigation when tiny/unknown rectangles cannot be hit.
3. **Freeware is not open source.** The supplied redtrillix repository contains
   executables/manuals, not reusable licensed source. Its Disclaimer explicitly
   says source is not free and prohibits modification/reverse engineering [3].
   No binary, source, asset or implementation was copied. The supplied .github
   profile and space-sniffer.com are secondary references, not author authority:
   their version/system-requirement statements differ from the developer's [2,4,5].
4. **Native totals exist locally but are private/version-dependent.** A read-only
   same-timestamp StorageManagementService log probe verified the Applications,
   Developer, Documents, Mail, OtherUsers, Music, CloudDocs and Photos extension
   fields. `System` and `Other` retain their original values. Additional fields
   (for example Messages) remain separate, never silently folded into System Data.
   Full raw logs and exact private paths stay under ignored `.private/`.

## Shared presentation contract

`domain/storage_map.py` owns MapEntry, category field labels, conservative display
estimates, overlap handling, disjoint selectable IDs and integer treemap geometry.
The TUI and Status JSON `storage_map` use this same hierarchy.

Top-level screenshot labels, in order:
Applications; Developer; Documents; iCloud Drive; Mail; Music; Photos;
Other Users & Shared; macOS; System Data.

- Native category blocks use recorded category totals and their own timestamp,
  never sums of filesystem paths normalized to a target total. Missing is unknown,
  not zero. Extra native categories retain separate labels.
- Clicking a category changes the area basis to **observed allocations; estimated
  category paths**. These child totals need not reconcile to the native block.
  Native-total blocks do not nest estimated children into their native area.
- Without native data, area is measured allocation in disjoint estimated groups.
  Inaccessible resources have no fabricated area; zero/unknown and tiny rectangles
  remain reachable in the list. Unattributed paths are separate, not blanket
  System Data. With native data Unattributed has no competing native area.
- Intermediate directory totals sum non-overlapping frontier nodes. A measured
  inclusive ancestor retains its allocation rather than adding descendants or
  redistributing those descendants into another category. Read-only drilldown
  archives that old parent measurement, removes its stale disposition/size and
  uses the new child inventory; it does not extend old candidate expiry.
- `◆` and green identify raw Laya remove recommendations; `◇` means a container
  **contains** recommendations, not that its whole subtree is disposable.
  Selected actual paths show `[x]` and amber. Keep/review and execution-unavailable
  targets never become selectable because of a color or category.
- `A`/`a` selects all currently known model-approved, execution-ready Trash paths
  across the inventory, independent of the open layer. Commands/categories are
  excluded. Parent/descendant overlap is removed. `N` clears, Space toggles the
  focused actual candidate. Clicking a recommended regular-file leaf toggles it;
  clicking directories opens/inventories children. `D` reviews selected paths.
- `D` uses the unchanged exact manifests/reassessment and final No-default dialog.
  No selection key or chart interaction cleans files automatically. Staging does
  not free space. Directory consent covers all descendants.

The path grouping function is **presentation-only** and is never imported by model
input, policy or executor adapters. It cannot grant cleanup approval. Canonical
namespace facts continue to reach Laya through existing dev4 evidence definitions.

## Verification and remaining gaps

RED-first coverage includes layout area/overlap, exact labels, separate recorded
and estimated values, nested measurements, stale parent replacement, JSON parity,
raw recommendations, tiny/unknown targets, mouse hit testing, nested back chains,
uppercase A, persistent selection, cancellation/No default and unchanged Clean.

A source-level read-only custom scope (Caches, Logs, Documents, Pictures) measured
191 resources in 17.462 seconds, 51 selectable actual resources and 2,013,700,096
allocated proposed bytes, zero measurement gaps and zero personal-folder proposals.
This custom scope is not startup-disk performance, exclusive reclaim or independent
cleanup safety validation. Files moved/prune commands: zero.

Actual installed dev5 read-only startup scope subsequently finished: 3,630 resources
discovered, 3,611 measured in 109.04 seconds, 44 measurement gaps, complete access
false. 84 selectable actual paths / 2,513,477,632 proposed allocated bytes, no command
rows and no Documents/Pictures/Desktop proposals in that run. Native ten categories,
Messages and separate Unattributed were present. Existing decisions/cache and a busy
workstation were reused; no cold-latency guarantee.

Actual installed TUI using that private report verified category labels/values, 84
selected IDs, selection preserved across 80×24 resize and back navigation, and amber
selection rendering. An actual installed threaded drilldown into a small resource
completed in 15.018 seconds, showed children immediately, preserved unrelated
selection and old plan age, and returned one level with Esc. Files moved/prune
calls: zero. Source/isolated-wheel installation verified pinned model readiness and
33 installed Python files matched the source. Final **316 tests / 82.56% coverage**, lint/type/architecture gates passed locally
and fresh frozen-Python-3.12 sdist. Final source and isolated wheel model readiness
and all 33 Python-file parity checks passed. Gate receipts are in VERIFICATION.md.

Apple's per-file membership, System Photo Library designation, exact Developer
scope, iCloud local-versus-cloud size, unreadable other-user data, APFS sharing and
category refresh lag remain limitations. Unknown native totals are not fabricated.
The terminal list is a keyboard alternative; no claim of full WCAG/screen-reader
conformance is made. Synthetic demo metadata uses real local Laya inference; it
is not a screenshot of private data or a canned model verdict.

## Sources (read 2026-10-10)

[1] Apple Support, [Change Storage settings on Mac](https://support.apple.com/guide/mac-help/change-storage-settings-mchl3d437fbc/mac), primary category definitions.

[2] Uderzo Umberto, [SpaceSniffer developer page](https://www.uderzo.it/main_products/space_sniffer/), primary interaction description.

[3] [SpaceSniffer Disclaimer](https://github.com/redtrillix/SpaceSniffer/blob/main/Disclaimer.txt), supplied distribution's license text; no reusable source license.

[4] [Supplied .github profile](https://github.com/SpaceSniffer-Treemap/.github/blob/main/profile/README.md), secondary marketing reference, not authoritative implementation/requirements.

[5] [Supplied space-sniffer.com](https://space-sniffer.com/), secondary reference; version claims differ from developer page.

[6] Textual [widgets](https://textual.textualize.io/guide/widgets/) and [Click events](https://textual.textualize.io/events/click/), checked against installed Textual 1.x code and real Pilot/rendered interactions.
