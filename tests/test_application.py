import json
from datetime import datetime, timedelta, timezone

import pytest

from jev_clean.application.service import audit, load_plan, save_plan
from jev_clean.infrastructure.update import latest_version


def test_demo_is_explicit_and_cannot_authorize_real_cleanup(tmp_path, neural_boundary):
    report = audit(tmp_path, "clean", demo=True)
    assert report.demo and "synthetic" in report.model_status.lower() and report.exploration["steps"]
    plan = tmp_path / "plan.json"
    save_plan(plan, report)
    with pytest.raises(ValueError, match="[Dd]emo"):
        load_plan(plan, tmp_path)


def test_forged_cross_home_and_expired_plans_rejected(tmp_path, neural_boundary):
    home = tmp_path / "home"
    home.mkdir()
    report = audit(home, "status", demo=True)
    report.demo = False
    plan = tmp_path / "plan.json"
    save_plan(plan, report)
    with pytest.raises(ValueError, match="[Hh]ome"):
        load_plan(plan, tmp_path / "different")
    value = report.to_dict()
    value["created_at"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    plan.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="[Ee]xpired"):
        load_plan(plan, home)


def test_update_rejects_untrusted_redirected_release_identity():
    with pytest.raises(ValueError):
        latest_version({"tag_name": "v0.2.0", "html_url": "https://evil.test/download"})
    assert (
        latest_version(
            {"tag_name": "v0.2.0", "html_url": "https://github.com/chengyixu/jev-clean/releases/tag/v0.2.0"}
        )
        == "0.2.0"
    )
