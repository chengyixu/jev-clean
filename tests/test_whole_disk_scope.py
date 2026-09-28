import os
from pathlib import Path

from jev_clean.domain.models import Decision


class Model:
    calls = 0

    def choose_directory(self, nodes, mode):
        return Decision("n0", {f"n{i}": 1.0 if i == 0 else 0.0 for i in range(len(nodes))}, "test-model", 1.0)

    def predict(self, item):
        self.calls += 1
        return Decision("remove", {"remove": 1.0, "keep": 0.0, "review": 0.0}, "test-model", 1.0)

    def classify(self, node):
        return Decision("data", {"data": 1.0}, "test-model", 1.0)


def test_all_regular_files_reach_model_before_guard_including_protected(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    home = tmp_path / "home"
    home.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    for name in ("source.py", "database.sqlite", "empty", "private.key"):
        (outside / name).write_bytes(b"" if name == "empty" else b"unique data")
    model = Model()
    report = investigate_disk(
        home, model, "clean", roots=[outside], state_dir=tmp_path / "state", open_paths=set()
    )
    assert report.stats["observed_regular_files"] == 4
    assert report.stats["model_assessed_files"] == 4
    assert report.stats["model_assessed_protected_files"] == 4
    assert not report.candidates
    assert report.stats["walk_finished"]


def test_no_600_file_cap_and_no_cache_root_restriction(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "not-a-cache"
    root.mkdir()
    for i in range(1100):
        (root / str(i)).write_bytes(b"x")
    report = investigate_disk(
        home, Model(), "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert report.stats["observed_regular_files"] == 1100
    assert report.stats["model_assessed_files"] == 1100
    assert report.stats["walk_finished"] and report.complete


def test_cache_reuse_is_counted_separately_and_still_covers_every_file(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "files"
    root.mkdir()
    for i in range(5):
        p = root / str(i)
        p.write_bytes(b"x")
        os.utime(p, (1_700_000_000, 1_700_000_000))
    model = Model()
    first = investigate_disk(
        home, model, "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    second = investigate_disk(
        home, model, "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert first.stats["model_assessed_files"] == second.stats["model_assessed_files"] == 5
    assert second.stats["fresh_model_inferences"] == 0
    assert second.stats["reused_model_decisions"] == 5


def test_cancellation_is_not_full_disk_completion(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "files"
    root.mkdir()
    for i in range(20):
        (root / str(i)).write_bytes(b"x")
    progress = []
    report = investigate_disk(
        home,
        Model(),
        "clean",
        roots=[root],
        state_dir=tmp_path / "state",
        open_paths=set(),
        cancelled=lambda: True,
        progress=progress.append,
    )
    assert not report.complete and not report.stats["walk_finished"]


def test_no_symlink_target_traversal(tmp_path):
    from jev_clean.application.whole_disk import investigate_disk

    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "other"
    outside.mkdir()
    (outside / "secret").write_text("keep")
    (root / "alias").symlink_to(outside, target_is_directory=True)
    report = investigate_disk(
        home, Model(), "clean", roots=[root], state_dir=tmp_path / "state", open_paths=set()
    )
    assert report.stats["observed_regular_files"] == 0
    assert report.stats["symlinks_observed"] == 1


def test_startup_scope_includes_system_data_and_other_mounted_container_volumes():
    from jev_clean.infrastructure.volumes import resolve_startup_scope

    root = {"APFSContainerReference": "disk1", "VolumeUUID": "system-id", "MountPoint": "/"}
    listing = {
        "Containers": [
            {
                "ContainerReference": "disk1",
                "Volumes": [
                    {"DeviceIdentifier": "disk1s1", "APFSVolumeUUID": "system-id", "Roles": ["System"]},
                    {"DeviceIdentifier": "disk1s5", "APFSVolumeUUID": "data-id", "Roles": ["Data"]},
                    {"DeviceIdentifier": "disk1s6", "APFSVolumeUUID": "vm-id", "Roles": ["VM"]},
                    {"DeviceIdentifier": "disk1s3", "APFSVolumeUUID": "recovery-id", "Roles": ["Recovery"]},
                ],
            }
        ]
    }
    info = {
        "disk1s1": {"MountPoint": "/System/Volumes/Update/mnt1"},
        "disk1s5": {"MountPoint": "/System/Volumes/Data"},
        "disk1s6": {"MountPoint": "/System/Volumes/VM"},
        "disk1s3": {},
    }
    scope = resolve_startup_scope(root, listing, info)
    assert set(scope.roots) == {Path("/"), Path("/System/Volumes/Data"), Path("/System/Volumes/VM")}
    assert scope.exclusions and "unmounted" in str(scope.exclusions)
