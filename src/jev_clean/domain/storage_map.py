"""Storage presentation only: Apple labels, explicitly estimated path groups and geometry.

Namespace estimates never affect learned dispositions or execution readiness. Native
category totals and measured path allocations intentionally use different bases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePath

from jev_clean.domain.models import AuditReport, Candidate

CATEGORY_FIELDS = {
    "Applications": "com.apple.STMExtension.Applications",
    "Developer": "com.apple.STMExtension.Developer",
    "Documents": "com.apple.STMExtension.Documents",
    "iCloud Drive": "com.apple.CloudDocsDaemon.StorageManagement",
    "Mail": "com.apple.STMExtension.Mail",
    "Music": "com.apple.Music.MusicStorageExtension",
    "Photos": "com.apple.Photos.StorageManagementExtension",
    "Other Users & Shared": "com.apple.STMExtension.OtherUsers",
    "macOS": "System",
    "System Data": "Other",
}
EXTRA_FIELDS = {
    "com.apple.messages.StorageManagementExtension": "Messages",
    "com.apple.STMExtension.iOSFiles": "iOS Files",
    "com.apple.STMExtension.Trash": "Trash",
    "com.apple.STMExtension.GarageBand": "Music Creation",
}
OBSERVED = "observed allocation; estimated category"


@dataclass
class MapEntry:
    id: str
    label: str
    allocated_bytes: int | None
    basis: str = OBSERVED
    path: str = ""
    is_dir: bool = False
    complete: bool = True
    candidate_id: str = ""
    recommended: bool = False
    contains_recommendations: bool = False
    children: list[MapEntry] = field(default_factory=list)


@dataclass(frozen=True)
class Tile:
    entry: MapEntry
    x: int
    y: int
    width: int
    height: int

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


def path_group(path: str, home: str) -> tuple[str, str]:
    """Conservative namespace estimates, NOT Apple's private per-file assignments."""
    p, h = PurePath(path), PurePath(home)
    anchors = [
        ("iCloud Drive", h / "Library/Mobile Documents/com~apple~CloudDocs"),
        ("Mail", h / "Library/Mail"),
        ("Music", h / "Music/Music"),
        ("Developer", h / "Library/Developer"),
        ("Developer", PurePath("/Library/Developer")),
        ("Applications", h / "Applications"),
        ("Applications", PurePath("/Applications")),
        ("Other Users & Shared", PurePath("/Users/Shared")),
    ]
    for name, root in anchors:
        if p.is_relative_to(root):
            return name, str(root)
    if p.is_relative_to(h / "Pictures") and any(s.endswith(".photoslibrary") for s in p.parts):
        return "Photos", str(h / "Pictures")
    for root in [h / s for s in ("Documents", "Desktop", "Downloads", "Movies", "Pictures")]:
        if p.is_relative_to(root):
            return "Documents", str(root)
    if p.is_relative_to("/Users") and not p.is_relative_to(h) and p != PurePath("/Users"):
        return "Other Users & Shared", "/Users"
    if (
        p.is_relative_to("/System/Library")
        or p.is_relative_to("/System/Applications")
        or p == PurePath("/System")
    ):
        return "macOS", "/System"
    for root in [h / "Library", PurePath("/Library"), PurePath("/private/var"), h / ".cache"]:
        if p.is_relative_to(root):
            return "System Data", str(root)
    # Nonhidden direct HOME data is a Documents estimate; opaque dot-trees are unknown.
    if p.is_relative_to(h) and p != h and not p.relative_to(h).parts[0].startswith("."):
        return "Documents", str(h)
    return "Unattributed", str(p.parent)


def _summarize(entry: MapEntry) -> None:
    for child in entry.children:
        _summarize(child)
    if entry.children:
        if entry.allocated_bytes is None and any(c.allocated_bytes is not None for c in entry.children):
            entry.allocated_bytes = sum(c.allocated_bytes or 0 for c in entry.children)
        entry.complete &= all(c.complete for c in entry.children)
        entry.contains_recommendations = any(
            c.recommended or c.contains_recommendations for c in entry.children
        )
        entry.children.sort(key=lambda c: (-(c.allocated_bytes or 0), c.label, c.id))


def storage_map(report: AuditReport) -> MapEntry:
    root = MapEntry(
        "disk",
        "Storage",
        None,
        "observed allocation; estimated categories",
        is_dir=True,
        complete=bool(report.coverage.get("complete", report.exploration.get("complete", True))),
    )
    categories = {name: MapEntry("category:" + name, name, None, is_dir=True) for name in CATEGORY_FIELDS}
    root.children = list(categories.values())
    categories["Unattributed"] = MapEntry("category:Unattributed", "Unattributed", None, is_dir=True)
    entries: dict[tuple[str, str], MapEntry] = {}
    candidates = {c.path: c for c in report.scan.candidates if c.operation == "trash"}
    nodes = {n["path"]: n for n in report.exploration.get("nodes", [])}
    for path, n in sorted(nodes.items(), key=lambda pair: (len(PurePath(pair[0]).parts), pair[0])):
        name, anchor = path_group(path, report.home)
        # A recorded ancestor owns its inclusive allocation. Do not redistribute
        # nested observations into another category and count the bytes twice.
        ancestors = [a for a in PurePath(path).parents if str(a) in nodes]
        if ancestors:
            name, anchor = path_group(str(ancestors[-1]), report.home)
        category = categories[name]
        parent = category
        p, a = PurePath(path), PurePath(anchor)
        # Keep namespace context and every intermediate directory navigable.
        chain = [a] if p == a or (name, str(a)) in entries else []
        current = a
        for part in p.relative_to(a).parts:
            current /= part
            chain.append(current)
        for part_path in chain:
            key = (name, str(part_path))
            if key not in entries:
                e = MapEntry(
                    "path:" + str(part_path),
                    part_path.name or str(part_path),
                    None,
                    path=str(part_path),
                    is_dir=True,
                )
                entries[key] = e
                parent.children.append(e)
            parent = entries[key]
        amount = n.get("allocated_bytes")
        parent.allocated_bytes = amount if isinstance(amount, int) and amount >= 0 else None
        parent.complete = bool(n.get("complete", False))
        parent.is_dir = bool(n.get("is_dir"))
        parent.recommended = bool((n.get("decision") or {}).get("choice") == "remove")
        c = candidates.get(path)
        if c:
            parent.candidate_id = c.id
            parent.recommended = bool(c.decision and c.decision.choice == "remove")
    for category in categories.values():
        _summarize(category)
    if report.categories:
        native = report.categories
        root.basis = "recorded macOS totals + separate observed paths"
        for name, field_name in CATEGORY_FIELDS.items():
            e = categories[name]
            value = (
                native.system_bytes
                if field_name == "System"
                else native.other_bytes
                if field_name == "Other"
                else native.named.get(field_name)
            )
            e.allocated_bytes = value
            e.basis = "recorded macOS total" if value is not None else "macOS total unavailable"
        for field_name, value in native.named.items():
            if field_name not in CATEGORY_FIELDS.values():
                label = EXTRA_FIELDS.get(field_name, field_name)
                root.children.append(MapEntry("native:" + field_name, label, value, "recorded macOS total"))
    if categories["Unattributed"].children:
        if report.categories:
            # Reachable via keyboard/list, but not mixed into recorded-total area.
            categories["Unattributed"].allocated_bytes = None
            categories["Unattributed"].basis = "separate observed paths; no native category attribution"
        root.children.append(categories["Unattributed"])
    # Do not sum independent recorded totals together with filesystem allocations.
    root.complete &= all(c.complete for c in root.children)
    root.contains_recommendations = any(c.recommended or c.contains_recommendations for c in root.children)
    return root


def recommended_ids(items: list[Candidate]) -> set[str]:
    chosen: list[Candidate] = []
    for c in sorted(items, key=lambda c: (len(PurePath(c.path).parts), c.path)):
        if (
            c.selectable
            and c.operation == "trash"
            and not any(PurePath(c.path).is_relative_to(x.path) for x in chosen)
        ):
            chosen.append(c)
    return {c.id for c in chosen}


def toggle_selection(selected: set[str], item: Candidate, items: list[Candidate]) -> set[str]:
    if not item.selectable or item.operation != "trash":
        return set(selected)
    if item.id in selected:
        return selected - {item.id}
    targets = {c.id: PurePath(c.path) for c in items}
    p = PurePath(item.path)
    return {
        i
        for i in selected
        if i in targets and not (p.is_relative_to(targets[i]) or targets[i].is_relative_to(p))
    } | {item.id}


def layout_tiles(entries: list[MapEntry], width: int, height: int) -> list[Tile]:
    """Deterministic balanced binary treemap; round at splits, never overlap.

    Geometry uses terminal cell aspect ratio (~2 pixels high per width). Unknown
    and zero measurements have no invented area; they stay reachable in the list.
    """
    positive = sorted(
        [e for e in entries if e.allocated_bytes is not None and e.allocated_bytes > 0],
        key=lambda e: (-(e.allocated_bytes or 0), e.id),
    )
    result: list[Tile] = []

    def divide(group: list[MapEntry], x: int, y: int, w: int, h: int) -> None:
        if not group or w <= 0 or h <= 0:
            return
        if len(group) == 1 or (w == 1 and h == 1):
            result.append(Tile(group[0], x, y, w, h))
            return
        total = sum(e.allocated_bytes or 0 for e in group)
        cumulative = 0
        splits = []
        for i, e in enumerate(group[:-1], 1):
            cumulative += e.allocated_bytes or 0
            splits.append((abs(total / 2 - cumulative), i, cumulative))
        _, index, first = min(splits)
        if (w >= h * 2 and w > 1) or h == 1:
            cut = max(1, min(w - 1, round(w * first / total)))
            divide(group[:index], x, y, cut, h)
            divide(group[index:], x + cut, y, w - cut, h)
        else:
            cut = max(1, min(h - 1, round(h * first / total)))
            divide(group[:index], x, y, w, cut)
            divide(group[index:], x, y + cut, w, h - cut)

    divide(positive, 0, 0, max(0, width), max(0, height))
    return result
