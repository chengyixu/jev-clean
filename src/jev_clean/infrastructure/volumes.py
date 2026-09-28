"""Discover the startup APFS container without mounting anything or guessing /Users is the disk."""

import plistlib
from dataclasses import dataclass, field
from pathlib import Path

from jev_clean.infrastructure.native import run


@dataclass
class DiskScope:
    roots: list[Path]
    exclusions: list[dict] = field(default_factory=list)
    kind: str = "startup-disk"


def resolve_startup_scope(root_info: dict, listing: dict, infos: dict) -> DiskScope:
    container = root_info.get("APFSContainerReference")
    roots = [Path("/")]
    exclusions = []
    current_uuid = root_info.get("VolumeUUID") or root_info.get("APFSVolumeUUID")
    matched = False
    for item in listing.get("Containers", []):
        if item.get("ContainerReference") != container:
            continue
        matched = True
        for volume in item.get("Volumes", []):
            device = volume["DeviceIdentifier"]
            boot_device = root_info.get("DeviceIdentifier", "")
            represented_system = "System" in volume.get("Roles", []) and (
                boot_device == device or boot_device.startswith(device + "s")
            )
            if (
                represented_system
                or volume.get("APFSVolumeUUID") == current_uuid
                or (not current_uuid and not boot_device and "System" in volume.get("Roles", []))
            ):
                continue  # The booted system snapshot is already represented by /.
            mount = infos.get(device, {}).get("MountPoint")
            if mount:
                roots.append(Path(mount))
            else:
                exclusions.append(
                    {"device": device, "reason": "unmounted or locked startup volume; not mounted by scanner"}
                )
    if not matched:
        raise RuntimeError(
            "Cannot establish startup-disk volume scope; no partial root-only fallback. Retry or explicitly choose --root."
        )
    return DiskScope(list(dict.fromkeys(roots)), exclusions)


def normalize_roots(roots: list[Path]) -> list[Path]:
    selected: list[Path] = []
    for root in sorted(set(roots), key=lambda p: (len(p.parts), str(p))):
        if root == Path("/System/Volumes/Data") and Path("/") in roots:
            selected.append(root)
            continue  # System walk explicitly prunes firmlinks covered by this scope.
        redundant = False
        for parent in selected:
            if not root.is_relative_to(parent):
                continue
            try:
                device = parent.stat().st_dev
                chain = [root, *root.parents]
                chain = chain[: chain.index(parent) + 1]
                redundant = all(p.stat().st_dev == device for p in chain)
            except OSError:
                redundant = False
            if redundant:
                break
        if not redundant:
            selected.append(root)
    return selected


def startup_scope() -> DiskScope:
    def query(*args):
        code, out, _ = run(["/usr/sbin/diskutil", *args], 15)
        if code:
            return {}
        try:
            return plistlib.loads(out.encode())
        except (ValueError, plistlib.InvalidFileException):
            return {}

    root_info = query("info", "-plist", "/")
    listing = query("apfs", "list", "-plist")
    infos = {}
    for container in listing.get("Containers", []):
        if container.get("ContainerReference") == root_info.get("APFSContainerReference"):
            for volume in container.get("Volumes", []):
                device = volume["DeviceIdentifier"]
                infos[device] = query("info", "-plist", device)
    return resolve_startup_scope(root_info, listing, infos)
