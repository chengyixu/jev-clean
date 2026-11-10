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


def _drain(selector, buffers: dict[str, bytearray], bound: int, until: float) -> None:
    while selector is not None and selector.get_map() and time.monotonic() < until:
        for key, _ in selector.select(min(0.1, max(0.0, until - time.monotonic()))):
            chunk = os.read(key.fd, 65536)
            if not chunk:
                selector.unregister(key.fileobj)
            elif len(buffers[key.data]) < bound:
                buffers[key.data].extend(chunk)


def _stop(process, selector, buffers: dict[str, bytearray], bound: int, *, drain_seconds: float = 2) -> None:
    """Stop a reader without raising: never re-read pipes a stuck child or grandchild still holds."""
    if process.poll() is None:
        # sudo relays SIGTERM to its root-owned reader; SIGKILL to sudo would orphan that reader.
        process.terminate()
    _drain(selector, buffers, bound, time.monotonic() + drain_seconds)
    if process.poll() is None and process.args[0] != "/usr/bin/sudo":
        process.kill()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass  # uninterruptible kernel I/O; the scan keeps its partial data instead of blocking


def _collect(
    command: list[str], timeout: float, cancelled, on_line, bound: int
) -> tuple[int, bytes, bytes, int]:
    """Bounded native reader. Returns (returncode, stdout, stderr, stopped) where stopped is 0/124/130."""
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as error:
        return 127, b"", str(error).encode(), 0
    assert process.stdout is not None and process.stderr is not None
    buffers = {"out": bytearray(), "err": bytearray()}
    pending = b""
    deadline = time.monotonic() + timeout
    stopped = 0
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "out")
            selector.register(process.stderr, selectors.EVENT_READ, "err")
            try:
                while selector.get_map() and not stopped:
                    if cancelled():
                        stopped = 130
                        break
                    if time.monotonic() >= deadline:
                        stopped = 124
                        break
                    for key, _ in selector.select(0.1):
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        buffers[key.data].extend(chunk)
                        if len(buffers[key.data]) > bound:
                            stopped = 124
                            break
                        if key.data == "out" and on_line is not None:
                            pending += chunk
                            while b"\n" in pending:
                                line, pending = pending.split(b"\n", 1)
                                on_line(line.decode("utf-8", errors="replace"))
                if not stopped:
                    # Both pipes closed; a child that keeps running without them is still bounded.
                    try:
                        process.wait(timeout=max(0.1, deadline - time.monotonic()))
                    except subprocess.TimeoutExpired:
                        stopped = 124
            except BaseException:
                _stop(process, selector, buffers, bound)
                raise
            if stopped:
                _stop(process, selector, buffers, bound)
    finally:
        process.stdout.close()
        process.stderr.close()
    return process.returncode, bytes(buffers["out"]), bytes(buffers["err"]), stopped


def run(argv: list[str], timeout: float = 30) -> tuple[int, str, str]:
    # System-wide lsof prints several MB; the bound only stops a runaway reader.
    code, out, err, stopped = _collect(argv, timeout, lambda: False, None, 64 * 1024 * 1024)
    text_out = out.decode("utf-8", errors="replace")
    text_err = err.decode("utf-8", errors="replace")
    if stopped:
        return stopped, text_out, text_err + f"\nTimeout after {timeout}s; partial output retained"
    return code, text_out, text_err


def memory_pressure() -> int:
    """macOS kernel memory pressure level: 1 normal, 2 warn, 4 critical. One syscall, no process."""
    import ctypes

    level = ctypes.c_int(0)
    size = ctypes.c_size_t(ctypes.sizeof(level))
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.sysctlbyname(
        b"kern.memorystatus_vm_pressure_level", ctypes.byref(level), ctypes.byref(size), None, 0
    ):
        raise OSError(ctypes.get_errno(), "kern.memorystatus_vm_pressure_level unavailable")
    return level.value


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
    from jev_clean.infrastructure.paths import firmlinks, logical_path

    mappings = firmlinks()
    return {str(logical_path(Path(line[1:]), mappings)) for line in out.splitlines() if line.startswith("n/")}


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
    """Native du with bounded capture and cancellation; no shell or daemon."""
    code, raw_out, raw_err, stopped = _collect(command, timeout, cancelled, on_line, 4 * 1024 * 1024)
    out = raw_out.decode("utf-8", errors="replace")
    err = raw_err.decode("utf-8", errors="replace")
    if stopped:
        err += "\nTimeout/cancel/output bound; partial data retained"
    return stopped or code, out, err


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
