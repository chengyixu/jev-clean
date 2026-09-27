from dataclasses import replace

import pytest

from jev_clean.domain.models import Candidate, Decision, Fingerprint
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.model import parse_prediction
from jev_clean.infrastructure.native import parse_categories


def candidate(**changes):
    item = Candidate(
        "id",
        "/Users/example/Library/Caches/test/blob",
        "user-cache",
        4096,
        8640000,
        Fingerprint(1, 2, 4096, 1, 1, 501, 1),
        True,
        False,
        True,
    )
    return replace(item, **changes)


def test_model_cannot_override_unsafe_files():
    for changes in (
        {"regular": False},
        {"symlink": True},
        {"scan_complete": False},
        {"open_file": True},
        {"open_file": None},
        {"age_seconds": 2},
        {"kind": "database"},
        {"fingerprint": Fingerprint(1, 2, 4096, 1, 1, 501, 2)},
    ):
        result = apply_policy(
            candidate(**changes), Decision("remove", {"remove": 0.99, "keep": 0.01}, "laya", 1)
        )
        assert not result.eligible
        assert result.reason


def test_low_confidence_or_keep_predictions_never_recommend():
    for decision in [
        Decision("keep", {"keep": 1.0}, "laya", 1),
        Decision("remove", {"remove": 0.4, "keep": 0.6}, "laya", 1),
    ]:
        result = apply_policy(candidate(open_file=False), decision)
        assert not result.recommended


def test_eligible_is_separate_from_model_recommendation():
    item = candidate(open_file=False)
    assert apply_policy(item, None).eligible
    assert not apply_policy(item, None).recommended
    assert apply_policy(item, Decision("remove", {"remove": 0.95, "keep": 0.05}, "laya", 1)).recommended


def test_native_report_never_merges_timestamps_or_guesses_missing_categories():
    def line(time, key, n):
        return f"2026-09-27 {time} Df x StorageLogInvestigation - {key}: {n}"

    text = "\n".join(
        [
            line("10:00:00.000", "Used", 100),
            line("10:00:00.000", "System", 10),
            line("10:00:00.000", "com.apple.STMExtension.Documents", 40),
            line("10:00:00.000", "Other", 50),
            line("10:00:01.000", "Used", 900),
        ]
    )
    report = parse_categories(text)
    assert report and report.other_bytes == 50 and report.residual_bytes == 50
    assert report.timestamp == "2026-09-27 10:00:00.000"
    assert parse_categories(line("10:00:00.000", "Used", 100)) is None


def test_category_mismatch_is_not_hidden():
    text = "\n".join(
        f"2026-09-27 10:00:00.000 StorageLogInvestigation - {k}: {v}"
        for k, v in {"Used": 100, "System": 10, "com.apple.STMExtension.Documents": 40, "Other": 60}.items()
    )
    report = parse_categories(text)
    assert report and report.discrepancy_bytes == 10


def test_invalid_model_output_fails_closed():
    for raw in [
        {},
        {"answers": {"disposition": {"choice": "rm -rf /"}}},
        {"answers": {"disposition": {"choice": "remove", "probabilities": {"remove": float("nan")}}}},
    ]:
        with pytest.raises(ValueError):
            parse_prediction(raw, 3.0, "laya")


def test_model_output_is_validated_and_preserved():
    result = parse_prediction(
        {
            "answers": {
                "disposition": {
                    "choice": "review",
                    "probabilities": {"remove": 0.1, "keep": 0.2, "review": 0.7},
                }
            }
        },
        4.5,
        "laya",
    )
    assert result.choice == "review" and result.elapsed_ms == 4.5
    assert result.probabilities["review"] == 0.7
