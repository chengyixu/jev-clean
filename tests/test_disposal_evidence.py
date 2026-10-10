"""Cache declarations remain observations, never Laya admission overrides."""

import pytest
from test_model_owned_judgment import answer

from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.resources import measure_resource

SIGNATURE = b"Signature: 8a477f597d28d172789f06886806bc55"


@pytest.mark.parametrize(
    "name",
    ["Pictures", "Documents", "Desktop", "Downloads", "projects", "renamed-user-data", "cache-looking-name"],
)
def test_application_does_not_reclassify_model_answer_using_folder_name(tmp_path, name):
    path = tmp_path / name
    path.mkdir()
    (path / "fixture.bin").write_bytes(b"synthetic")
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    assert item.disposal is None
    assert apply_policy(item, answer("remove")).selectable
    assert not apply_policy(item, answer("review")).selectable
    # Real-model personal controls are validated separately, not a boundary double.


def test_observed_cache_declaration_cannot_override_model_keep(tmp_path):
    path = tmp_path / "arbitrary-location"
    path.mkdir()
    (path / "CACHEDIR.TAG").write_bytes(SIGNATURE)
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    assert item.disposal is not None
    assert apply_policy(item, answer("remove")).selectable
    assert not apply_policy(item, answer("keep")).selectable
    assert not apply_policy(item, answer("review")).selectable


@pytest.mark.parametrize("content", [b"", b"cache", b" " + SIGNATURE, SIGNATURE.lower()])
def test_invalid_marker_is_not_reported_as_observed_declaration(tmp_path, content):
    path = tmp_path / "generated"
    path.mkdir()
    (path / "CACHEDIR.TAG").write_bytes(content)
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    assert item.disposal is None
    assert "none observed" in item.evidence["disposal_basis"]


def test_symlinked_declaration_is_not_reported_as_owner_fact(tmp_path):
    path = tmp_path / "generated"
    path.mkdir()
    marker = tmp_path / "other"
    marker.write_bytes(SIGNATURE)
    (path / "CACHEDIR.TAG").symlink_to(marker)
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    assert item.disposal is None
