"""Status category attribution is display evidence, never cleanup authorization."""

from dataclasses import replace
from importlib import import_module
from importlib.util import find_spec

import pytest

from jev_clean.domain.models import AuditReport, Candidate, CategoryReport, Decision, Fingerprint, ScanReport

LABELS = (
    "Applications",
    "Developer",
    "Documents",
    "iCloud Drive",
    "Mail",
    "Music",
    "Photos",
    "Other Users & Shared",
    "macOS",
    "System Data",
)


def contract():
    assert find_spec("jev_clean.domain.storage_map"), (
        "Status needs a shared typed hierarchy, not flat percentage rows"
    )
    return import_module("jev_clean.domain.storage_map")


def item(path, choice="remove", *, ready=True, operation="trash"):
    return Candidate(
        path,
        path,
        "unknown",
        200,
        0,
        Fingerprint(1, 2, 200, 0, 0, 501, 1),
        False,
        False,
        True,
        eligible=ready,
        recommended=choice == "remove",
        unit="directory",
        operation=operation,
        decision=Decision(choice, {choice: 1}, "test", 0),
    )


def report():
    paths = [
        "/Applications/Editor.app",
        "/Users/test/Library/Developer/Xcode/DerivedData/one",
        "/Users/test/Library/Caches/browser",
        "/Users/test/Documents/book",
        "/Users/test/.unknown/data",
    ]
    return AuditReport(
        1,
        "2026-10-10T10:00:00Z",
        "/Users/test",
        "status",
        ScanReport([item(p) for p in paths]),
        categories=CategoryReport(
            "2026-10-10 09:00:00.000",
            2000,
            100,
            {
                "com.apple.STMExtension.Applications": 400,
                "com.apple.STMExtension.Documents": 800,
                "com.apple.STMExtension.Developer": 200,
            },
            500,
        ),
        exploration={
            "nodes": [{"path": p, "allocated_bytes": 200, "is_dir": True, "complete": True} for p in paths]
        },
    )


def test_exact_category_names_and_separate_native_sizes():
    m = contract().storage_map(report())
    assert tuple(n.label for n in m.children[:10]) == LABELS
    apps = next(n for n in m.children if n.label == "Applications")
    assert apps.allocated_bytes == 400 and apps.basis == "recorded macOS total"
    assert sum(n.allocated_bytes or 0 for n in apps.children) == 200
    assert apps.children[0].path == "/Applications/Editor.app"
    assert apps.children[0].basis == "observed allocation; estimated category"
    assert m.children[-1].label == "Unattributed"
    assert m.children[-1].children[0].path == "/Users/test/.unknown/data"


def test_unknown_native_category_not_silently_folded_into_system_data():
    r = report()
    r.categories = replace(
        r.categories, named={**r.categories.named, "com.apple.messages.StorageManagementExtension": 17}
    )
    m = contract().storage_map(r)
    assert next(n for n in m.children if n.label == "Messages").allocated_bytes == 17
    assert next(n for n in m.children if n.label == "System Data").allocated_bytes == 500


def test_missing_totals_not_zero_and_hierarchy_no_nested_double_count():
    r = report()
    r.categories = None
    r.exploration["nodes"].append(
        {
            "path": "/Users/test/Library/Caches/browser/nested",
            "allocated_bytes": 100,
            "is_dir": True,
            "complete": True,
        }
    )
    m = contract().storage_map(r)
    assert next(n for n in m.children if n.label == "Mail").allocated_bytes is None
    assert next(n for n in m.children if n.label == "System Data").allocated_bytes == 200
    assert m.basis == "observed allocation; estimated categories"
    developer = next(n for n in m.children if n.label == "Developer")
    assert developer.children and developer.children[0].children


def test_selection_excludes_commands_keep_review_blocked_and_overlaps():
    mod = contract()
    items = [
        item("/cache"),
        item("/cache/child"),
        item("/other"),
        item("/keep", "keep"),
        item("/review", "review"),
        item("/blocked", ready=False),
        item("/command", operation="owner_prune"),
    ]
    assert mod.recommended_ids(items) == {"/cache", "/other"}
    assert mod.toggle_selection({"/cache", "/other"}, items[1], items) == {"/cache/child", "/other"}


@pytest.mark.parametrize("width,height", [(80, 20), (120, 35), (1, 1), (0, 20)])
def test_treemap_tiles_cover_area_without_overlaps(width, height):
    mod = contract()
    tiles = mod.layout_tiles(
        [mod.MapEntry(str(i), str(i), n) for i, n in enumerate([60, 25, 10, 5])], width, height
    )
    occupied = set()
    for tile in tiles:
        assert tile.width > 0 and tile.height > 0
        cells = {
            (x, y) for x in range(tile.x, tile.x + tile.width) for y in range(tile.y, tile.y + tile.height)
        }
        assert not occupied & cells
        occupied |= cells
        assert 0 <= tile.x < width and 0 <= tile.y < height
    assert len(occupied) == width * height
    if width >= 80:
        assert abs(tiles[0].width * tiles[0].height / (width * height) - 0.6) < 0.04
        assert max(t.width / (t.height * 2) for t in tiles) < 8


def test_gap_has_no_fabricated_area_but_remains_in_hierarchy():
    mod = contract()
    r = report()
    r.exploration["nodes"].append(
        {
            "path": "/Users/test/Library/Logs/denied",
            "allocated_bytes": None,
            "is_dir": True,
            "complete": False,
        }
    )
    m = mod.storage_map(r)
    system = next(n for n in m.children if n.label == "System Data")
    assert not system.complete
    assert any(not n.complete for n in system.children)
    assert not mod.layout_tiles([mod.MapEntry("unknown", "unknown", None)], 80, 20)
