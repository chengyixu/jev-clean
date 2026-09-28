import pytest

from jev_clean.infrastructure.volumes import resolve_startup_scope


def test_scope_discovery_failure_does_not_silently_scan_only_system_root():
    with pytest.raises(RuntimeError, match="startup"):
        resolve_startup_scope({}, {}, {})
