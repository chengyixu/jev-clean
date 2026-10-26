"""The real Status pipeline must retain actual learned recommendations."""

from dataclasses import replace

from jev_clean.application.resources import investigate_resources
from jev_clean.infrastructure.model import LayaAdvisor


def test_status_retains_file_candidates_and_model_decisions(tmp_path, neural_boundary):
    root = tmp_path / "Library/Caches/test"
    root.mkdir(parents=True)
    (root / "cache.bin").write_bytes(b"payload")
    result = investigate_resources(tmp_path, LayaAdvisor(), "status", roots=[root], open_paths=set())
    assert result.candidates, "Status loses learned recommendations, so its map cannot color/select them"
    assert result.candidates[0].operation == "trash" and result.candidates[0].selectable
    assert result.nodes[0].decision and result.nodes[0].decision.choice == "remove"
    assert result.stats["approved_candidate_bytes"] > 0


def test_status_demo_keeps_real_model_candidates(tmp_path, neural_boundary):
    from jev_clean.application.service import audit

    r = audit(tmp_path, "status", demo=True)
    assert r.scan.candidates, "Synthetic Status must exercise real recommendations too"
    assert all(c.decision for c in r.scan.candidates)


def test_expansion_merges_snapshot_preserving_unrelated_selection(tmp_path):
    from test_status_map_contract import item

    from jev_clean.application import service
    from jev_clean.domain.models import AuditReport, ScanReport

    assert hasattr(service, "merge_status"), "Drilldown must not discard prior recommendations and navigation"
    old = AuditReport(
        1,
        "old",
        str(tmp_path),
        "status",
        ScanReport([item("/a"), item("/b")]),
        exploration={
            "nodes": [
                {"path": "/a", "allocated_bytes": 200, "is_dir": True, "complete": True},
                {"path": "/b", "allocated_bytes": 200, "is_dir": True, "complete": True},
            ]
        },
    )
    new = replace(
        old,
        created_at="new",
        scan=ScanReport([item("/a/one")]),
        exploration={"nodes": [{"path": "/a/one", "allocated_bytes": 200, "is_dir": True, "complete": True}]},
    )
    combined = service.merge_status(old, new, "/a")
    assert {c.path for c in combined.scan.candidates} == {"/b", "/a/one"}
    assert {n["path"] for n in combined.exploration["nodes"]} == {"/a", "/b", "/a/one"}
    assert combined.created_at == "old", "Drilldown must not extend the age of old actionable metadata"
