import pytest
from test_contracts import candidate
from test_model_owned_judgment import answer

from jev_clean.infrastructure import model


@pytest.mark.parametrize("label", ["remove", "review", "keep"])
def test_model_adapter_answer_is_preserved_without_tag_reclassification(monkeypatch, label):
    monkeypatch.setattr(model.LayaAdvisor, "_shared", object())
    monkeypatch.setattr(model, "predict_cleanup", lambda backend, item: answer(label))
    result = model.LayaAdvisor().predict(candidate(disposal=None))
    assert result.choice == label
    assert result.probabilities[label] == 1.0
    assert set(result.probabilities) == {"keep", "review", "remove"}
