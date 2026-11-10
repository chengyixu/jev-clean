"""v9 observations: facts the v8 input silently lost, and inputs that depended on scan order."""

import os
from dataclasses import replace

import pytest
from test_contracts import candidate

from jev_clean.infrastructure import evidence, learned_cleanup, model


def resource(evidence_facts):
    return candidate(unit="directory", regular=False, evidence=evidence_facts)


def test_a_git_directory_is_observed_as_a_repository_marker(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "README").write_text("x")
    observed = evidence.observe_children(tmp_path)
    assert ".git:1" in observed["directory_extensions"]
    text = learned_cleanup.observed_state(resource(observed))
    assert "source or repository formats" in text


def test_dotfile_names_are_their_own_token_and_dotted_dotfiles_keep_their_suffix(tmp_path):
    (tmp_path / ".DS_Store").write_text("x")
    (tmp_path / ".env.local").write_text("x")
    files = evidence.observe_children(tmp_path)["file_extensions"]
    assert ".ds_store:1" in files and ".local:1" in files and "[none]" not in files


def test_equal_counts_are_listed_in_name_order_whatever_the_scan_order(tmp_path, monkeypatch):
    for name in ("b.zz", "a.yy", "c.xx"):
        (tmp_path / name).write_text("x")
    first = evidence.observe_children(tmp_path)
    real = os.scandir

    class Reversed:
        def __init__(self, fd):
            self.inner = real(fd)

        def __enter__(self):
            return reversed(list(self.inner.__enter__()))

        def __exit__(self, *exc):
            return self.inner.__exit__(*exc)

    monkeypatch.setattr(evidence.os, "scandir", Reversed)
    second = evidence.observe_children(tmp_path)
    assert first == second
    assert first["file_extensions"] == ".xx:1, .yy:1, .zz:1"


CANONICAL = [
    ("Library/Application Support/MobileSync/Backup/0000", "ios-device-backup"),
    ("Library/Developer/Xcode/DerivedData/App-abc", "xcode-derived-data"),
    ("Library/Developer/Xcode/iOS DeviceSupport/18.1 (22B83)", "xcode-device-support"),
    ("Library/Developer/Xcode/watchOS DeviceSupport/11.0", "xcode-device-support"),
    ("Library/Developer/Xcode/Archives/2026-01-01", "xcode-archives"),
    ("Library/Developer/CoreSimulator/Devices/ABC", "simulator-devices"),
    ("Downloads/installer", "user-downloads"),
    ("Library/Mail/V10", "mail-store"),
    ("Library/Messages/Attachments", "messages-store"),
    ("Library/Mobile Documents/com~apple~CloudDocs", "icloud-drive"),
    (".ssh", "credential-store"),
    (".gnupg/private-keys-v1.d", "credential-store"),
]


@pytest.mark.parametrize(("relative", "role"), CANONICAL)
def test_canonical_storage_roots_are_observed_with_their_documented_purpose(tmp_path, relative, role):
    path = tmp_path / relative
    path.mkdir(parents=True)
    facts = evidence.observe_storage_role(path, tmp_path)
    assert facts["storage_namespace"] == role
    text = learned_cleanup.observed_state(resource(facts))
    assert facts["namespace_contract"] in text
    assert "Filesystem storage purpose is unverified" not in text


@pytest.mark.parametrize(
    "relative",
    ["Projects/Downloads", "Library/Developer/Xcode/DerivedDataOld", "Documents/.ssh-notes", "Mail"],
)
def test_lookalike_names_outside_canonical_roots_stay_unverified(tmp_path, relative):
    path = tmp_path / relative
    path.mkdir(parents=True)
    assert evidence.observe_storage_role(path, tmp_path)["storage_namespace"] == "unverified"


def test_every_storage_role_has_one_contract_used_by_observation_and_by_the_model_input():
    assert set(evidence.STORAGE_ROLES) >= {role for _, role in CANONICAL} | {
        "macos-cache",
        "macos-diagnostic-log",
    }
    for role, (label, contract) in evidence.STORAGE_ROLES.items():
        text = learned_cleanup.observed_state(resource({"storage_namespace": role}))
        assert f"Actual filesystem namespace: {label}. {contract}" in text


def test_the_resource_own_suffix_is_a_recognized_format_but_never_a_raw_token(tmp_path):
    library = tmp_path / "Pictures/Family.photoslibrary"
    (library / "database").mkdir(parents=True)
    facts = {**evidence.EvidenceCollector(tmp_path).collect(library), **evidence.observe_children(library)}
    assert facts["extension"] == ".photoslibrary"
    assert "media or photo-library formats" in learned_cleanup.observed_state(resource(facts))
    bundle = {**facts, "extension": ".chrome"}
    assert ".chrome" not in learned_cleanup.observed_state(resource(bundle))


def test_scan_and_selection_refresh_give_the_model_the_same_input(tmp_path, monkeypatch, neural_boundary):
    from test_model_owned_judgment import answer

    from jev_clean.application import service
    from jev_clean.infrastructure.model import LayaAdvisor, state_for
    from jev_clean.infrastructure.resources import measure_resource

    library = tmp_path / "Pictures/Family.photoslibrary"
    (library / "database").mkdir(parents=True)
    (library / "originals").mkdir()
    item = measure_resource(library, tmp_path, evidence.EvidenceCollector(tmp_path), set())
    monkeypatch.setattr(service.native, "open_files", lambda: set())
    seen = []
    monkeypatch.setattr(LayaAdvisor, "predict", lambda self, fresh: seen.append(fresh) or answer("remove"))
    service.prepare_selection([item], home=tmp_path)
    assert seen[0].evidence["extension"] == ".photoslibrary"
    assert state_for(seen[0]) == state_for(item)


@pytest.mark.parametrize(
    ("suffixes", "phrase"),
    [
        (".pdf:3, .docx:1", "document formats"),
        (".pages:1", "document formats"),
        (".zip:2", "archive formats"),
        (".tar:1, .7z:1", "archive formats"),
        (".gpg:1", "credential or recovery-related formats"),
        (".keychain-db:1", "credential or recovery-related formats"),
        (".emlx:40", "mail or message formats"),
        (".vmdk:1", "model or disk-image formats"),
        (".flac:12", "media or photo-library formats"),
        (".xcodeproj:1", "source or repository formats"),
    ],
)
def test_common_personal_formats_are_recognized(suffixes, phrase):
    text = learned_cleanup.observed_state(resource({"file_extensions": suffixes}))
    assert phrase in text
    assert "no recognized user-data format" not in text


def test_the_input_contract_names_the_v9_observations():
    assert model.INPUT_CONTRACT == "learned-file-purpose-structural-observations-v9"


def test_renaming_the_path_does_not_change_the_model_input():
    item = resource(
        {"storage_namespace": "xcode-derived-data", "extension": ".noindex", "file_extensions": ".o:3"}
    )
    moved = replace(item, path="/elsewhere/CHOOSE_A", id="other")
    assert learned_cleanup.observed_state(item) == learned_cleanup.observed_state(moved)


def test_the_model_input_lists_extensions_in_one_canonical_order_whoever_wrote_them():
    authored = resource({"file_extensions": ".tag:1, .json:2, .bin:1", "directory_extensions": ".b:1, .a:1"})
    canonical = resource({"file_extensions": ".json:2, .bin:1, .tag:1", "directory_extensions": ".a:1, .b:1"})
    assert learned_cleanup.observed_state(authored) == learned_cleanup.observed_state(canonical)
