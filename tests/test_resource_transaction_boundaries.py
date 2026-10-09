import pytest

from jev_clean.infrastructure.trash import TrashStore


@pytest.mark.parametrize("relative", [".", ".local", ".local/state", ".Trash", ".Trash/batch"])
def test_resource_cannot_contain_or_be_inside_executor_transaction_paths(tmp_path, relative):
    store = TrashStore(tmp_path)
    with pytest.raises(ValueError, match="journal|Trash"):
        store.validate_source(tmp_path / relative)
