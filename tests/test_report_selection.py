from jev_clean.application.service import audit
from jev_clean.domain.models import Candidate


def test_wire_report_exposes_selectable_without_trusting_imported_flag(tmp_path, neural_boundary):
    report = audit(tmp_path, "clean", demo=True).to_dict()
    for item in report["scan"]["candidates"]:
        assert "selectable" in item
        parsed = Candidate.from_dict({**item, "selectable": True})
        assert parsed.selectable == (parsed.eligible and parsed.recommended and parsed.decision is not None)
