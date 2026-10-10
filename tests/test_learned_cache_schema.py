"""Actual learned question, not historical base prompt, must namespace inference cache."""

from test_model_owned_judgment import answer
from test_whole_disk_scope import Model

from jev_clean.infrastructure import decision_cache


def test_changing_learned_question_cannot_reuse_previous_output(tmp_path, monkeypatch):
    assert hasattr(decision_cache, "CLEANUP_QUESTION")
    with decision_cache.DecisionCache(tmp_path / "state", Model(), [tmp_path], "clean") as cache:
        cache.put("same observation", answer("remove"))
    monkeypatch.setattr(
        decision_cache,
        "CLEANUP_QUESTION",
        {
            "type": "choice",
            "instructions": "new learned observation question",
            "criteria": {"A": "new", "B": "different", "C": "other"},
        },
    )
    with decision_cache.DecisionCache(tmp_path / "state", Model(), [tmp_path], "clean") as cache:
        assert cache.get("same observation") is None
