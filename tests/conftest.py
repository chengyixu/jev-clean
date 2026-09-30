"""The external neural boundary is substituted only in hermetic tests, never in production/demo."""

from pathlib import Path

import pytest

from jev_clean.domain.models import Decision
from jev_clean.infrastructure.model import LayaAdvisor


@pytest.fixture(autouse=True)
def isolate_host_application_manifests(monkeypatch):
    """Synthetic HOME manifests stay real; never enumerate the host's installed apps."""
    glob = Path.glob

    def fixture_glob(path, pattern, *args, **kwargs):
        if path == Path("/Applications"):
            return iter(())
        return glob(path, pattern, *args, **kwargs)

    monkeypatch.setattr(Path, "glob", fixture_glob)


def prediction(choice="remove"):
    return Decision(
        choice,
        {k: 0.96 if k == choice else 0.02 for k in ("remove", "review", "keep")},
        "test neural boundary",
        1.2,
    )


@pytest.fixture
def neural_boundary(monkeypatch):
    monkeypatch.setattr(LayaAdvisor, "load", lambda self: None)
    monkeypatch.setattr(
        LayaAdvisor,
        "choose_directory",
        lambda self, nodes, mode: Decision(
            "n0", {f"n{i}": 1.0 if i == 0 else 0.0 for i in range(len(nodes))}, "test neural boundary", 1.0
        ),
    )
    monkeypatch.setattr(
        LayaAdvisor,
        "inspect",
        lambda self, node, mode: Decision(
            "inspect", {"inspect": 0.9, "skip": 0.1}, "test neural boundary", 1.0
        ),
    )
    monkeypatch.setattr(
        LayaAdvisor,
        "classify",
        lambda self, node: Decision(
            "cache", {"cache": 0.8, "logs": 0.1, "data": 0.05, "unknown": 0.05}, "test neural boundary", 1.1
        ),
    )
    monkeypatch.setattr(LayaAdvisor, "predict", lambda self, item: prediction())
