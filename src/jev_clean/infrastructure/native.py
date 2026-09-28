"""Read-only native macOS diagnostics. All subprocesses are argv lists."""

from __future__ import annotations

import os
import platform
import re
import selectors
import stat
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        process = subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace"
        )
    except OSError as error:
        return 127, "", str(error)
    try:
        out, err = process.communicate(timeout=timeout)
        return process.returncode, out, err
    except subprocess.TimeoutExpired:
        # SIGTERM lets a sudo wrapper forward cancellation to its owned reader.
        process.terminate()
        try:
            out, err = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            out, err = process.communicate(timeout=2)
        return 124, out, err + f"\nTimeout after {timeout}s; partial output retained"


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


def open_files(*, deep: bool = False) -> set[str] | None:
    executable = "/usr/sbin/lsof" if platform.system() == "Darwin" else "/usr/bin/lsof"
    command = [executable, "-nP", "-Fn"]
    if deep:
        command = ["/usr/bin/sudo", "-n", *command]
    code, out, err = run(command, timeout=15)
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


def parse_du_tree(root: str, code: int, out: str, err: str) -> list[Measurement]:
    base = Path(root)
    values: dict[str, int] = {}
    for line in out.splitlines(keepends=True):
        if code in (124, 130) and not line.endswith("\n"):
            continue
        amount, separator, name = line.rstrip("\n").partition("\t")
        reported_path = Path(name)
        if separator and amount.strip().isdigit() and (reported_path == base or reported_path.parent == base):
            values[str(reported_path)] = int(amount) * 1024
    error_paths = []
    for line in err.splitlines():
        match = re.match(r"^du: (.*): [^:]+$", line)
        if match:
            error_paths.append(Path(match[1]))
    unknown_error = code not in (0, 124, 130) and not error_paths
    rows = []
    for path, size in values.items():
        incomplete = unknown_error or any(p == Path(path) or p.is_relative_to(path) for p in error_paths)
        if path == str(base) and code != 0:
            incomplete = True
        rows.append(
            Measurement(
                path,
                size,
                not incomplete,
                "Completed native subtree"
                if not incomplete
                else "Partial native measurement; permission/IO gap",
            )
        )
    if str(base) not in values:
        lower_bound = sum(values.values()) if values else None
        rows.insert(
            0,
            Measurement(
                str(base),
                lower_bound,
                False,
                "Partial: timeout/cancel/permission gap; sum of reported direct children only",
            ),
        )
    return rows


def _stream_du(command: list[str], timeout: float, cancelled, on_line) -> tuple[int, str, str]:
    """Foreground native du with bounded capture and cancellation; no shell or daemon."""
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as error:
        return 127, "", str(error)
    buffers = {"out": bytearray(), "err": bytearray()}
    pending = b""
    started = time.monotonic()
    stopped = 0
    assert process.stdout is not None and process.stderr is not None
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ, "out")
        selector.register(process.stderr, selectors.EVENT_READ, "err")
        while selector.get_map():
            if cancelled() or time.monotonic() - started >= timeout:
                stopped = 130 if cancelled() else 124
                process.terminate()
                break
            for key, _ in selector.select(0.1):
                chunk = os.read(key.fd, 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffers[key.data].extend(chunk)
                if len(buffers[key.data]) > 4 * 1024 * 1024:
                    stopped = 124
                    process.terminate()
                    break
                if key.data == "out":
                    pending += chunk
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        try:
                            on_line(line.decode("utf-8", errors="replace"))
                        except BaseException:
                            process.kill()
                            process.communicate(timeout=2)
                            raise
            if stopped:
                break
    try:
        tail_out, tail_err = process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        tail_out, tail_err = process.communicate(timeout=2)
    buffers["out"].extend(tail_out or b"")
    buffers["err"].extend(tail_err or b"")
    out = buffers["out"].decode("utf-8", errors="replace")
    err = buffers["err"].decode("utf-8", errors="replace")
    if stopped:
        err += "\nTimeout/cancel/output bound; partial data retained"
    return stopped or process.returncode, out, err


def measure_tree(
    path: Path, *, timeout: float = 60, deep: bool = False, progress=lambda _: None, cancelled=lambda: False
) -> list[Measurement]:
    from jev_clean.domain.models import human_bytes
    from jev_clean.infrastructure.scanner import no_symlink_ancestors

    if not no_symlink_ancestors(path):
        return [Measurement(str(path), None, False, "Symlink path refused")]

    def observed(line):
        size, sep, name = line.partition("\t")
        if sep and size.isdigit():
            progress(f"Measured {Path(name).name}: {human_bytes(int(size) * 1024)}")

    progress(f"Measuring {path}…")
    names = {
        "/Library": "system-library",
        "/private/var": "private-var",
        "/opt/homebrew/var": "homebrew-data",
    }
    if deep and str(path) in names:
        code, out, err = run(["/usr/bin/sudo", "-n", *DEEP_COMMANDS[names[str(path)]]], timeout)
        for line in out.splitlines():
            observed(line)
    else:
        code, out, err = _stream_du(
            ["/usr/bin/du", "-x", "-k", "-d", "1", str(path)], timeout, cancelled, observed
        )
    return parse_du_tree(str(path), code, out, err)


def measure_children(
    path: Path, *, timeout: float = 60, progress=lambda _: None, cancelled=lambda: False
) -> list[Measurement]:
    """Isolate slow HOME children so one huge tree cannot hide every other size."""
    from jev_clean.domain.models import human_bytes
    from jev_clean.infrastructure.scanner import no_symlink_ancestors

    if not no_symlink_ancestors(path):
        return [Measurement(str(path), None, False, "Symlink root refused")]
    rows = [Measurement(str(path), None, False, "Child inventory: no unique whole-root total claimed")]
    directories: list[Path] = []
    started = time.monotonic()
    try:
        device = path.stat().st_dev
        with os.scandir(path) as entries:
            for entry in entries:
                if len(rows) + len(directories) >= 1500:
                    break
                try:
                    st = entry.stat(follow_symlinks=False)
                except OSError:
                    rows.append(Measurement(entry.path, None, False, "Changed or inaccessible entry"))
                    continue
                if st.st_dev != device or stat.S_ISLNK(st.st_mode):
                    continue
                if stat.S_ISDIR(st.st_mode):
                    directories.append(Path(entry.path))
                elif stat.S_ISREG(st.st_mode):
                    rows.append(
                        Measurement(entry.path, st.st_blocks * 512, True, "Regular-file allocated blocks")
                    )
    except OSError:
        pass

    def one(child):
        if cancelled() or time.monotonic() - started >= timeout:
            return Measurement(str(child), None, False, "Inventory budget/cancel boundary")
        return measure(child, timeout=min(5, max(0.1, timeout - (time.monotonic() - started))))

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(one, child) for child in directories]
        for future in as_completed(futures):
            result = future.result()
            rows.append(result)
            if result.allocated_bytes is not None:
                progress(f"Measured {Path(result.path).name}: {human_bytes(result.allocated_bytes)}")
    return rows


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
