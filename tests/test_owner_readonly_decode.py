"""Process observations cannot crash the scan on non-UTF8 command bytes."""

from subprocess import CompletedProcess

from jev_clean.infrastructure import owner_tools


def test_readonly_owner_probe_decodes_invalid_command_text_safely(monkeypatch):
    seen = []

    def run(argv, **kwargs):
        seen.append(kwargs)
        assert kwargs.get("errors") == "replace"
        return CompletedProcess(argv, 0, stdout="process \ufffd", stderr="")

    monkeypatch.setattr(owner_tools.subprocess, "run", run)
    code, out, err = owner_tools.readonly_run(["/bin/ps", "-axo", "pid,ppid,comm,args"])
    assert code == 0 and "\ufffd" in out and not err
