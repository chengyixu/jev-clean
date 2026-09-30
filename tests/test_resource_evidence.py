"""Facts must distinguish different resources without inventing disposability."""

import plistlib

from jev_clean.infrastructure.model import state_for
from jev_clean.infrastructure.scanner import candidate_from_stat


def state(path, home):
    return state_for(candidate_from_stat(path, path.stat(), home, set()))


def test_model_sees_resource_context_extension_and_unknown_dependencies(tmp_path):
    path = tmp_path / "Library/Application Support/com.example.remote/Logs/private-session.xlog"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"never disclose content")
    text = state(path, tmp_path)
    assert "com.example.remote" in text and "Logs" in text and ".xlog" in text
    assert "private-session" not in text and "never disclose content" not in text
    assert "regenerability=unknown" in text and "references=unknown" in text
    assert str(tmp_path) not in text
    assert "preserve it" not in text and "protected" not in text


def test_same_size_age_but_distinct_resource_context_no_longer_collide(tmp_path):
    states = []
    for relative in ("Library/Application Support/demo/vm.raw", "Library/Logs/demo/current.xlog"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(b"equal")
        states.append(state(path, tmp_path))
    assert states[0] != states[1]


def test_installed_app_metadata_is_evidence_not_deletion_permission(tmp_path):
    info = tmp_path / "Applications/Demo.app/Contents/Info.plist"
    info.parent.mkdir(parents=True)
    info.write_bytes(
        plistlib.dumps({"CFBundleIdentifier": "com.example.demo", "CFBundleShortVersionString": "2.3"})
    )
    path = tmp_path / "Library/Application Support/com.example.demo/old.sqlite"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"not inspected")
    text = state(path, tmp_path)
    assert "com.example.demo" in text and "2.3" in text
    assert "identifier match" in text
    assert "references=unknown" in text


def test_absent_app_match_is_unknown_not_uninstalled(tmp_path):
    path = tmp_path / "Library/Application Support/unknown-app/blob"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"x")
    text = state(path, tmp_path)
    assert "application=unknown" in text
    assert "uninstalled" not in text
