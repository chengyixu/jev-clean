"""Owner-native cleanup observations: no deletion or model answer here.

Detect exact installed tools/cache paths and published command semantics. These
are model INPUTS, not permission gates; unsupported detection is absence of facts.
No automatic package installation, force flags, corepack network or cleanup calls.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path


def readonly_run(argv):
    env = {**os.environ, "COREPACK_ENABLE_NETWORK": "0", "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0"}
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=5, env=env)
        return result.returncode, result.stdout, result.stderr
    except (OSError, subprocess.TimeoutExpired):
        return 1, "", "owner tool unavailable"


def process_conflict(name, text, *, current_pid):
    records = {}
    for line in text.splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) == 4 and parts[0].isdigit() and parts[1].isdigit():
            records[int(parts[0])] = (int(parts[1]), parts[2], parts[3])
    ignored = set()
    pid = current_pid
    while pid in records and pid not in ignored:
        ignored.add(pid)
        pid = records[pid][0]
    return any(
        pid not in ignored
        and (Path(comm).name == name or re.search(rf"/{re.escape(name)}(?:\.cjs)?(?:\s|$)", args))
        for pid, (_, comm, args) in records.items()
    )


def active_owner(name):
    """Report unknown if process visibility fails; no in-use facts fabricated."""
    result = readonly_run(["/bin/ps", "-axo", "pid,ppid,comm,args"])
    if result[0]:
        return None
    return process_conflict(name, result[1], current_pid=os.getpid())


def owner_observations(executables=None, *, run=readonly_run, active=active_owner):
    executables = (
        {name: shutil.which(name) for name in ("uv", "pnpm")} if executables is None else executables
    )
    out = []
    for name, executable in executables.items():
        if not executable or name not in ("uv", "pnpm"):
            continue
        path_cmd = [executable, "cache", "dir"] if name == "uv" else [executable, "store", "path"]
        help_cmd = (
            [executable, "cache", "prune", "--help"] if name == "uv" else [executable, "store", "--help"]
        )
        code, text, error = run(path_cmd)
        path = Path(text.strip())
        if (
            code
            or error.strip()
            or not path.is_absolute()
            or ".." in path.parts
            or not path.is_dir()
            or path.is_symlink()
        ):
            continue
        code, helptext, _ = run(help_cmd)
        phrase = "Prune all unreachable objects from the cache" if name == "uv" else "Removes unreferenced"
        if code or phrase.lower() not in helptext.lower():
            continue
        use = active(name)
        activity = (
            "An active owner-tool process is observed; current cleanup conflict/needed objects require investigation."
            if use is True
            else "No active owner-tool process is observed. This is a point-in-time observation."
            if use is False
            else "Active owner-tool process use is unknown."
        )
        executable = str(Path(executable).resolve())
        argv = [executable, "cache", "prune"] if name == "uv" else [executable, "store", "prune"]
        state = (
            f"Observed operation: {name} owner-native cache/store prune without force. This is the installed storage owner's supported command, NOT whole-directory deletion. "
            "The tool's own path-discovery command identifies the exact current storage. The command selects only unused or unreferenced regenerable objects and coordinates with its owner storage locks; required projects and unique user work are not targeted. "
            f"{activity} This proposed operation targets no-longer-needed generated entries, not the entire resource. Exact removed bytes are unknown in advance; allocation is only an upper bound."
        )
        out.append(
            {
                "owner": name,
                "path": str(path),
                "argv": argv,
                "operation": "owner_prune",
                "state": state,
                "active": use,
                "contract_source": "https://docs.astral.sh/uv/concepts/cache/"
                if name == "uv"
                else "https://pnpm.io/cli/store",
            }
        )
    return out
