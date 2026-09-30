import types

import pytest

from jev_clean.infrastructure.model import LayaAdvisor


class Tokenizer:
    mask_token = "[MASK]"

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": list(range(len(text)))}


def test_overflowing_evidence_is_not_silently_truncated(monkeypatch):
    calls = []
    raw = {"answers": {"test": {"choice": "keep", "probabilities": {"keep": 1.0}}}}
    backend = types.SimpleNamespace(
        tok=Tokenizer(),
        cfg={"max_len": 10},
        prepare=lambda *a: ([{"ids": [1, 2, 3]}], []),
        predict=lambda *a: calls.append(a) or raw,
    )
    monkeypatch.setattr(LayaAdvisor, "_shared", backend)
    with pytest.raises(ValueError, match="context"):
        LayaAdvisor().decide("x" * 8, "test", "Question", {"keep": "Retain"})
    assert not calls
    assert LayaAdvisor().decide("x" * 7, "test", "Question", {"keep": "Retain"}).choice == "keep"
