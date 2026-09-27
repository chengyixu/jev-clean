from jev_clean.domain.usage import usage_rows


def node(path, size, complete=True):
    return {"path": path, "allocated_bytes": size, "complete": complete, "is_dir": True}


def test_root_percentage_does_not_add_child_bytes_twice():
    nodes = [
        node("/home", 500),
        node("/home/cache", 300),
        node("/home/work", 200),
        node("/opt", 300),
        node("/var", 200),
    ]
    rows = usage_rows(nodes)
    assert {r.path: r.percent for r in rows} == {"/home": 50.0, "/opt": 30.0, "/var": 20.0}
    child = usage_rows(nodes, parent="/home")
    assert {r.path: r.percent for r in child} == {"/home/cache": 60.0, "/home/work": 40.0}


def test_unknown_and_partial_are_not_given_fake_percentage():
    rows = usage_rows([node("/known", 500), node("/denied", None, False), node("/partial", 100, False)])
    values = {r.path: r.percent for r in rows}
    assert values == {"/known": 100.0, "/denied": None, "/partial": None}


def test_zero_and_duplicate_paths_do_not_break_share_calculation():
    rows = usage_rows([node("/a", 0), node("/a", 0), node("/b", 0)])
    assert len(rows) == 2 and all(r.percent == 0.0 for r in rows)
