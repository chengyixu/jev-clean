import os
from dataclasses import replace

from cache_fixtures import declare_cache
from test_model_owned_judgment import answer

from jev_clean.domain.models import DisposalEvidence
from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure.disposal import observe_disposal
from jev_clean.infrastructure.evidence import EvidenceCollector
from jev_clean.infrastructure.resources import measure_resource


def test_unrelated_scope_claim_does_not_authorize_personal_directory(tmp_path):
    path = tmp_path / "personal"
    path.mkdir()
    item = measure_resource(path, tmp_path, EvidenceCollector(tmp_path), set())
    item = replace(item, disposal=DisposalEvidence("cachedir-tag-v1", str(tmp_path / "cache"), "a" * 64))
    result = apply_policy(item, answer("remove"))
    assert not result.selectable and result.decision.choice == "remove"


def test_hardlinked_tag_cannot_authorize_cleanup(tmp_path):
    declare_cache(tmp_path / "cache")
    os.link(tmp_path / "cache/CACHEDIR.TAG", tmp_path / "alias-tag")
    assert observe_disposal(tmp_path / "cache", tmp_path, directory=True) is None


def test_declaration_writable_by_others_is_not_trusted(tmp_path):
    declare_cache(tmp_path / "cache")
    (tmp_path / "cache/CACHEDIR.TAG").chmod(0o666)
    assert observe_disposal(tmp_path / "cache", tmp_path, directory=True) is None


def test_restoring_legacy_file_journal_does_not_require_disposal_evidence(tmp_path):
    # Recovery restores previously staged data; new admission rules cannot strand it.
    from dataclasses import asdict

    from jev_clean.infrastructure.scanner import fingerprint
    from jev_clean.infrastructure.trash import TrashStore, save_private

    path = tmp_path / "Documents/valuable"
    path.parent.mkdir()
    batch_id = "a" * 32
    token = "b" * 32
    staged = tmp_path / ".Trash" / f"jev-clean-{batch_id}" / token
    staged.parent.mkdir(parents=True)
    staged.write_bytes(b"restore old data")
    journal = {
        "schema_version": 1,
        "id": batch_id,
        "entries": [
            {
                "source": str(path),
                "file": token,
                "state": "staged",
                "fingerprint": asdict(fingerprint(staged.stat())),
                "bytes": 4096,
            }
        ],
    }
    save_private(tmp_path / ".local/state/jev-clean" / f"{batch_id}.json", journal)
    result = TrashStore(tmp_path).restore(batch_id)
    assert result.moved == 1, result.failed
    assert path.read_bytes() == b"restore old data"
