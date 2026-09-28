from pathlib import Path

from jev_clean.infrastructure.volumes import resolve_startup_scope


def test_booted_snapshot_represents_its_underlying_system_volume_once():
    root = {"APFSContainerReference": "disk3", "DeviceIdentifier": "disk3s1s1", "VolumeUUID": "snapshot-uuid"}
    listing = {
        "Containers": [
            {
                "ContainerReference": "disk3",
                "Volumes": [
                    {
                        "DeviceIdentifier": "disk3s1",
                        "APFSVolumeUUID": "different-system-uuid",
                        "Roles": ["System"],
                    },
                    {"DeviceIdentifier": "disk3s5", "APFSVolumeUUID": "data-uuid", "Roles": ["Data"]},
                ],
            }
        ]
    }
    scope = resolve_startup_scope(
        root,
        listing,
        {
            "disk3s1": {"MountPoint": "/System/Volumes/Update/mnt1"},
            "disk3s5": {"MountPoint": "/System/Volumes/Data"},
        },
    )
    assert scope.roots == [Path("/"), Path("/System/Volumes/Data")]
