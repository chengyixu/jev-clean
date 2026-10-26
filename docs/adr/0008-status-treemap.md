# ADR 0008 — Layered Status treemap with honest accounting

Status: accepted for local dev5, 2026-10-10.

## Context

The owner requested SpaceSniffer-style category blocks, Laya cleanup highlighting,
A selection and nested click navigation. This supersedes flat Status percentage
rows but does not replace the minimal actual-path Clean workflow. Apple categories
have recorded native totals without publicly documented per-file membership.

## Decision

Use a pure shared MapEntry hierarchy and independent integer balanced treemap
implementation in the existing Textual terminal app. Exact screenshot labels are
mapped to verified native log fields. Child namespace grouping is an explicitly
estimated presentation layer and cannot change model decisions/permissions.
Recorded native areas do not display estimated children filling those areas.
Drilldown shows observed allocations; unknown/unattributed values stay unknown or
separate. Preserve native extra categories and ancestor inclusive accounting.

Retain real Laya recommendations for Status; categories containing them are distinct
from individually recommended resources. A chooses disjoint, technically ready,
model-approved actual Trash paths. D calls the existing selection preparation,
manifest recheck and No-default final confirmation. Mouse navigation has list and
keyboard equivalents; tiny and unknown items are not given invented area.

## Consequences

The result is a terminal visualization, not a native GUI, a SpaceSniffer port,
Apple-equivalent classification or validated deletion-safety model. The current
Laya weights/input contract are unchanged. Read-only drilldown archives old parent
sizes/choices and does not refresh old actionable metadata expiry. No proprietary
code/assets were copied and no user files were cleaned during verification.

Sources, limitations and tests: [Status research](../STATUS-TREEMAP.md).
