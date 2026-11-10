"""A declared cache buried in an opaque project tree becomes its own resource.

Before, the default frontier measured the whole project as one opaque resource, so the
model never saw the declaration and the cache was never a candidate. Splitting changes
granularity only: every resource, including the cache, still gets a model judgment.
"""

from cache_fixtures import declare_cache
from test_whole_disk_scope import Model

from jev_clean.application.resources import investigate_resources


def scan(home, root):
    return investigate_resources(
        home, Model(), "status", roots=[root], state_dir=home / "state", open_paths=set()
    )


def test_a_declared_cache_inside_an_opaque_project_is_judged_on_its_own(tmp_path):
    root = tmp_path / "scope"
    app = root / "Projects/app"
    (app / "src").mkdir(parents=True)
    (app / "src/main.rs").write_text("fn main() {}")
    (app / "README").write_text("x")
    declare_cache(app / "target")
    (app / "target/blob").write_bytes(b"x" * 8192)
    (root / "Projects/notes").mkdir()
    result = scan(tmp_path, root)
    nodes = {n.path for n in result.nodes}
    assert str(app / "target") in nodes
    assert {str(app / "src"), str(app / "README"), str(root / "Projects/notes")} <= nodes
    # Opened ancestors are not also resources: nothing is measured twice.
    assert str(app) not in nodes and str(root / "Projects") not in nodes
    target = next(c for c in result.candidates if c.path == str(app / "target"))
    assert target.disposal is not None
    assert result.stats["walk_finished"]
    assert result.stats["declared_cache_splits"] == 1


def test_only_the_outermost_declaration_is_a_resource(tmp_path):
    root = tmp_path / "scope"
    outer = root / "work/build"
    declare_cache(outer)
    declare_cache(outer / "inner")
    result = scan(tmp_path, root)
    nodes = {n.path for n in result.nodes}
    assert str(outer) in nodes and str(outer / "inner") not in nodes


def test_an_invalid_marker_does_not_split_the_tree(tmp_path):
    root = tmp_path / "scope"
    project = root / "project"
    (project / "fake").mkdir(parents=True)
    (project / "fake/CACHEDIR.TAG").write_text("not a signature")
    result = scan(tmp_path, root)
    assert {n.path for n in result.nodes} == {str(project)}
    assert result.stats["declared_cache_splits"] == 0


def test_a_tree_without_markers_is_searched_once(tmp_path, monkeypatch):
    from jev_clean.infrastructure import resources

    root = tmp_path / "scope"
    declare_cache(root / "a/b/cache")
    (root / "a/b/plain/deep").mkdir(parents=True)
    (root / "a/other").mkdir()
    searched = []
    real = resources.nested_declarations
    monkeypatch.setattr(
        resources, "nested_declarations", lambda path, *a, **k: searched.append(path) or real(path, *a, **k)
    )
    scan(tmp_path, root)
    # Only the top resource is searched; its children are known to be searched already.
    assert searched == [root / "a"]
