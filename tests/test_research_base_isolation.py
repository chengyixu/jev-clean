"""Training baselines must not silently inherit the now-adapted app model."""

import importlib.util
from pathlib import Path


def test_research_loader_uses_verified_base_without_runtime_adapter(monkeypatch, tmp_path):
    path = Path(__file__).resolve().parents[1] / "scripts/laya_research_base.py"
    assert path.exists(), "Base research loader missing"
    spec = importlib.util.spec_from_file_location("research_base", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from jev_clean.infrastructure import model

    calls = []
    monkeypatch.setattr(model, "prepare_checkpoint", lambda: calls.append("base integrity") or tmp_path)
    import sys
    import types

    backend = object()
    monkeypatch.setitem(
        sys.modules, "laya_mlx", types.SimpleNamespace(load=lambda p: calls.append(p) or backend)
    )
    monkeypatch.setattr(
        model,
        "load_cleanup_adapter",
        lambda *a: (_ for _ in ()).throw(AssertionError("base research must not load trained adapter")),
    )
    assert m.load_research_base() is backend
    assert calls == ["base integrity", str(tmp_path)]
