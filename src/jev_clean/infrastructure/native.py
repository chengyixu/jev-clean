"""Read-only native macOS diagnostics. All subprocesses are argv lists."""

from __future__ import annotations

import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

import psutil

from jev_clean.domain.models import CategoryReport, Measurement

# Privileged executions cannot be supplied by a model, report, path or UI input.
DEEP_COMMANDS = {
    "system-library": ["/usr/bin/du", "-x", "-k", "-d", "1", "/Library"],
    "private-var": ["/usr/bin/du", "-x", "-k", "-d", "1", "/private/var"],
    "homebrew-data": ["/usr/bin/du", "-x", "-k", "-d", "1", "/opt/homebrew/var"],
    "snapshots": ["/usr/sbin/diskutil", "apfs", "listSnapshots", "/System/Volumes/Data"],
    "categories": [
        "/usr/bin/log",
        "show",
        "--last",
        "20m",
        "--style",
        "compact",
        "--predicate",
        'process == "StorageManagementService"',
    ],
}


def run(argv: list[str], timeout: float = 30) -> tuple[int, str, str]:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Timeout after {timeout}s; coverage unavailable"
    except OSError as error:
        return 127, "", str(error)


def deep_probe(name: str) -> dict[str, Any]:
    if name not in DEEP_COMMANDS:
        raise ValueError("Unrecognized diagnostic")
    code, out, err = run(["/usr/bin/sudo", "-n", *DEEP_COMMANDS[name]], timeout=45)
    return {"returncode": code, "stdout": out, "stderr": err, "complete": code == 0}


def authorize() -> bool:
    """Called only with the real terminal suspended out of Textual. No password pipe."""
    if platform.system() != "Darwin":
        return False
    return subprocess.run(["/usr/bin/sudo", "-v"], check=False).returncode == 0


def open_files() -> set[str] | None:
    executable = "/usr/sbin/lsof" if platform.system() == "Darwin" else "/usr/bin/lsof"
    code, out, err = run([executable, "-nP", "-Fn"], timeout=15)
    if code != 0 or err.strip():
        return None
    return {line[1:] for line in out.splitlines() if line.startswith("n/")}


def parse_categories(text: str) -> CategoryReport | None:
    groups: dict[str, dict[str, int]] = {}
    pattern = re.compile(
        r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+).*?"
        r"StorageLogInvestigation - (.+?): (-?\d+)\s*$"
    )
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            timestamp, name, value = match.groups()
            groups.setdefault(timestamp, {})[name] = int(value)
    for timestamp, values in reversed(list(groups.items())):
        if not {"Used", "System", "Other"}.issubset(values):
            continue
        named = {key: value for key, value in values.items() if key.startswith("com.apple.")}
        if not named or any(
            v < 0 for v in [*named.values(), values["Used"], values["System"], values["Other"]]
        ):
            continue
        return CategoryReport(timestamp, values["Used"], values["System"], named, values["Other"])
    return None


def measure(path: Path, *, timeout: float = 20) -> Measurement:
    code, out, err = run(["/usr/bin/du", "-x", "-k", "-s", str(path)], timeout)
    value: int | None = None
    for line in out.splitlines():
        size, _, _path = line.partition("\t")
        if size.strip().isdigit():
            value = int(size) * 1024
    return Measurement(
        str(path),
        value,
        code == 0,
        "Allocated blocks; not exclusive APFS reclaim or category membership"
        if code == 0
        else f"Partial/unavailable: {err[:180]}",
    )


def status_snapshot(home: Path) -> dict[str, Any]:
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(home))
    swap = psutil.swap_memory()
    return {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "load": list(os.getloadavg()),
        "memory_total": memory.total,
        "memory_available": memory.available,
        "memory_percent": memory.percent,
        "swap_used": swap.used,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "uptime_seconds": __import__("time").time() - psutil.boot_time(),
    }
