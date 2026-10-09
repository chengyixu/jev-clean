"""An arbitrary model remove is not independent evidence that data is disposable."""

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
def test_arbitrary_untagged_directory_is_not_selectable_even_if_model_says_remove(tmp_path, name):
    path = tmp_path / name
    path.mkdir()
    (path / "work.bin").write_bytes(b"irreplaceable")
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    result = apply_policy(item, answer("remove"))
    assert result.decision.choice == "remove"  # never conceal classifier mistakes
    assert not result.selectable
    assert "evidence" in result.reason.lower()


def test_valid_cache_declaration_can_support_model_proposal_without_a_path_allowlist(tmp_path):
    path = tmp_path / "arbitrary-location"
    path.mkdir()
    (path / "CACHEDIR.TAG").write_bytes(SIGNATURE + b"\n# generated cache\n")
    (path / "artifact").write_bytes(b"generated")
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    result = apply_policy(item, answer("remove"))
    assert getattr(result, "disposal", None) is not None
    assert result.selectable
    assert not apply_policy(item, answer("keep")).selectable
    assert not apply_policy(item, answer("review")).selectable


@pytest.mark.parametrize("content", [b"", b"cache", b" " + SIGNATURE, SIGNATURE.lower()])
def test_invalid_cache_marker_never_creates_disposal_evidence(tmp_path, content):
    path = tmp_path / "generated"
    path.mkdir()
    (path / "CACHEDIR.TAG").write_bytes(content)
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    assert not apply_policy(item, answer("remove")).selectable


def test_symlinked_declaration_is_not_trusted(tmp_path):
    path = tmp_path / "generated"
    path.mkdir()
    marker = tmp_path / "somewhere-else"
    marker.write_bytes(SIGNATURE)
    (path / "CACHEDIR.TAG").symlink_to(marker)
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    assert not apply_policy(item, answer("remove")).selectable
