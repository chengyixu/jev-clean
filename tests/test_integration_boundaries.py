import pytest

from jev_clean.application import service
from jev_clean.infrastructure import model, native


def test_native_diagnostics_report_timeout_and_missing_tool():
    code, out, err = native.run(["/definitely/not/a/tool"], timeout=1)
    assert code == 127 and not out and err
    code, out, err = native.run(["/bin/sleep", "2"], timeout=0.01)
    assert code == 124 and "Timeout" in err


def test_native_du_partial_is_visible(monkeypatch, tmp_path):
    monkeypatch.setattr(native, "run", lambda *a, **k: (1, f"4\t{tmp_path}\n", "Permission denied"))
    item = native.measure(tmp_path)
    assert item.allocated_bytes == 4096 and not item.complete and item.category_membership == "unattributed"


def test_native_open_files_fails_closed_on_warning(monkeypatch):
    monkeypatch.setattr(native, "run", lambda *a, **k: (0, "p12\nn/tmp/open\n", ""))
    assert native.open_files() == {"/tmp/open"}
    monkeypatch.setattr(native, "run", lambda *a, **k: (0, "n/tmp/open\n", "incomplete handles"))
    assert native.open_files() is None


def test_sudo_command_is_native_read_only(monkeypatch):
    calls = []

    def run(argv, timeout):
        calls.append(argv)
        return 1, "", "sudo: a password is required"

    monkeypatch.setattr(native, "run", run)
    assert not native.deep_probe("private-var")["complete"]
    assert calls == [["/usr/bin/sudo", "-n", "/usr/bin/du", "-x", "-k", "-d", "1", "/private/var"]]


def test_missing_model_fails_not_fallback(monkeypatch, tmp_path):
    def fail(self):
        raise RuntimeError("model not downloaded")

    monkeypatch.setattr(model.LayaAdvisor, "load", fail)
    with pytest.raises(RuntimeError, match="model not downloaded"):
        service.audit(tmp_path, "clean")


def test_model_authority_with_real_synthetic_files(monkeypatch, tmp_path, neural_boundary):
    p = tmp_path / "Library/Caches/com.test/item"
    p.parent.mkdir(parents=True)
    p.write_text("fixture")
    monkeypatch.setattr(native, "open_files", lambda: set())
    monkeypatch.setattr(native, "run", lambda *a, **k: (1, "", "unavailable"))
    report = service.audit(tmp_path, "clean", roots=[p.parent])
    assert report.scan.candidates[0].selectable
    assert report.exploration["stats"]["observed_files"] == 1
    assert report.exploration["stats"]["execution_unavailable"] == 0
    assert report.exploration["steps"][0]["children_seen"] == 1
    assert report.exploration["steps"][0]["decision"]["backend"] == "test neural boundary"


def test_cancelled_model_investigation_cannot_authorize(monkeypatch, tmp_path, neural_boundary):
    monkeypatch.setattr(native, "open_files", lambda: set())
    monkeypatch.setattr(native, "run", lambda *a, **k: (1, "", "unavailable"))
    report = service.audit(tmp_path, "clean", roots=[tmp_path], cancelled=lambda: True)
    assert not report.scan.complete and report.scan.warnings


def test_status_model_directed_and_private_raw_logs_discarded(monkeypatch, tmp_path, neural_boundary):
    (tmp_path / "one").mkdir()
    monkeypatch.setattr(native.platform, "system", lambda: "Darwin")
    calls = []

    def run(argv, timeout):
        calls.append(argv)
        return 1, "private paths", "not authorized"

    monkeypatch.setattr(native, "run", run)
    report = service.audit(tmp_path, "status", roots=[tmp_path], deep=True)
    assert report.exploration["steps"] and not report.scan.candidates
    assert report.categories is None
    assert "stdout" not in report.diagnostics["category_probe"]
    assert any(c[0] == "/usr/bin/sudo" for c in calls)


def test_malformed_model_distributions_fail_closed():
    for probs in [
        {"keep": 0.1, "remove": 2, "review": 0.2},
        {"keep": 0.1, "remove": 0.1, "review": 0.1},
        {"keep": 0.8, "remove": 0.1, "review": 0.1},
    ]:
        with pytest.raises(ValueError):
            model.parse_prediction(
                {"answers": {"disposition": {"choice": "remove", "probabilities": probs}}}, 1, "test"
            )
