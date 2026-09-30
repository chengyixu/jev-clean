import pytest
from test_contracts import candidate

from jev_clean.domain.models import Decision
from jev_clean.infrastructure.model import LayaAdvisor


@pytest.mark.parametrize("raw,label", [("A", "remove"), ("B", "review"), ("C", "keep")])
def test_neutral_label_is_translated_without_reclassification(monkeypatch, raw, label):
    def decide(self, state, key, instructions, criteria):
        return Decision(raw, {k: 1.0 if k == raw else 0.0 for k in ("A", "B", "C")}, "neural boundary", 7)

    monkeypatch.setattr(LayaAdvisor, "decide", decide)
    result = LayaAdvisor().predict(candidate())
    assert result.choice == label
    assert result.probabilities[label] == 1.0
    assert set(result.probabilities) == {"keep", "review", "remove"}
    assert result.elapsed_ms == 7
