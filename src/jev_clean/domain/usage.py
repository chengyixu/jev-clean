"""Percentage rows with an explicit measured-siblings basis, never nested double counting."""

from dataclasses import dataclass
from pathlib import PurePath


@dataclass(frozen=True)
class UsageRow:
    path: str
    allocated_bytes: int | None
    percent: float | None
    complete: bool
    is_dir: bool


def usage_rows(
    nodes: list[dict], parent: str | None = None, *, observed_basis: bool = False
) -> list[UsageRow]:
    unique = {str(PurePath(n["path"])): n for n in nodes}
    paths = {p for p in unique if parent is None or (p != parent and PurePath(p).is_relative_to(parent))}
    # Incomplete ancestors must not hide completed native child measurements.
    frontier = [p for p in paths if not any(str(a) in paths for a in PurePath(p).parents)]
    expanded = []
    gaps = []
    while frontier:
        p = frontier.pop(0)
        descendants = {x for x in paths if x != p and PurePath(x).is_relative_to(p)}
        children = [x for x in descendants if not any(str(a) in descendants for a in PurePath(x).parents)]
        if not unique[p].get("complete", False) and children:
            frontier.extend(children)
            gaps.append(UsageRow(p + " [unmeasured]", None, None, False, False))
        else:
            expanded.append(p)
    frontier = expanded

    def known(p: str) -> bool:
        return (
            (observed_basis or unique[p].get("complete", False))
            and isinstance(unique[p].get("allocated_bytes"), int)
            and unique[p]["allocated_bytes"] >= 0
        )

    total = sum(unique[p]["allocated_bytes"] for p in frontier if known(p))
    rows = [
        UsageRow(
            p,
            unique[p].get("allocated_bytes"),
            (100 * unique[p]["allocated_bytes"] / total if total else 0.0) if known(p) else None,
            bool(unique[p].get("complete")),
            bool(unique[p].get("is_dir")),
        )
        for p in frontier
    ]
    return sorted(rows + gaps, key=lambda r: (r.percent is None, -(r.allocated_bytes or 0), r.path))


def bar(percent: float | None, width: int = 14) -> str:
    if percent is None:
        return "─" * width
    filled = round(min(100.0, max(0.0, percent)) * width / 100)
    return "█" * filled + "░" * (width - filled)
