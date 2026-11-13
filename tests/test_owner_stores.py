"""An owner tool's stores are protected as soon as the tool reports where they live.

Live run on 2026-11-13: uv 0.13.6 reworded `uv cache prune --help`, the help phrase no
longer matched, uv went undetected, and ~/.cache/uv plus uv's installed tools in
~/.local/share/uv/tools were offered for the Trash. The help phrase only decides whether
the owner's own irreversible command is offered; it never decides store protection.
"""

from test_model_owned_judgment import answer

from jev_clean.application import service
from jev_clean.domain.policy import OWNER_STORE_ISSUE, apply_policy
from jev_clean.infrastructure import owner_tools
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.resources import measure_resource


def uv_layout(root):
    stores = {name: root / name for name in ("cache", "tools", "python")}
    for path in stores.values():
        path.mkdir(parents=True)
    replies = {
        ("cache", "dir"): stores["cache"],
        ("tool", "dir"): stores["tools"],
        ("python", "dir"): stores["python"],
    }

    def run(argv):
        if tuple(argv[1:]) in replies:
            return 0, f"{replies[tuple(argv[1:])]}\n", ""
        # uv 0.13.6 wording; the old phrase is gone.
        return 0, "Prune dangling cache entries and cached environments", ""

    return stores, run


def test_uv_stores_are_protected_whatever_its_help_text_says(tmp_path):
    stores, run = uv_layout(tmp_path)
    found = owner_tools.managed_stores({"uv": "/installed/uv"}, run=run)
    assert set(found) == set(stores.values())


def test_a_failed_location_query_invents_no_store(tmp_path):
    assert owner_tools.managed_stores({"uv": "/installed/uv"}, run=lambda argv: (1, "", "failed")) == []


def test_an_installed_tool_inside_a_managed_store_is_never_offered_for_the_trash(
    tmp_path, monkeypatch, neural_boundary
):
    stores, run = uv_layout(tmp_path / "uv")
    tool = stores["tools"] / "some-cli"
    (tool / "bin").mkdir(parents=True)
    monkeypatch.setattr(owner_tools, "managed_stores", lambda: [stores["tools"]])
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    item = apply_policy(
        measure_resource(tool, tmp_path, EvidenceCollector(tmp_path), set()), answer("remove")
    )
    sealed = service.prepare_selection([item], home=tmp_path)
    assert not sealed[0].selectable and sealed[0].execution_issue == OWNER_STORE_ISSUE
    result = service.execute_selection(sealed, home=tmp_path)
    assert result.moved == 0 and (tool / "bin").exists()


def test_a_scan_never_offers_a_managed_store_for_the_trash(tmp_path, monkeypatch):
    from test_whole_disk_scope import Model

    from jev_clean.application.resources import investigate_resources

    root = tmp_path / "scope"
    (root / "uv-tools/some-cli").mkdir(parents=True)
    (root / "uv-tools/some-cli/blob").write_bytes(b"x")
    (root / "other").mkdir()
    monkeypatch.setattr(owner_tools, "managed_stores", lambda: [root / "uv-tools"])
    result = investigate_resources(
        tmp_path, Model(), "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    store_rows = [c for c in result.candidates if c.path.startswith(str(root / "uv-tools"))]
    assert store_rows and all(c.execution_issue == OWNER_STORE_ISSUE for c in store_rows)


def test_a_whole_disk_plan_larger_than_16_mb_can_be_read(tmp_path):
    from jev_clean.infrastructure.trash import read_private, save_private

    path = tmp_path / "plan.json"
    save_private(path, {"rows": ["x" * 1000] * 20_000})
    assert path.stat().st_size > 16 * 1024 * 1024
    assert len(read_private(path)["rows"]) == 20_000
