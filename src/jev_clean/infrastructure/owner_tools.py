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
from typing import Any

# Typed owner interfaces, not folder classification/approval rules. Detection,
# documented semantics and argv share one definition used at scan/apply/staging.
OWNER_INTERFACES: dict[str, dict[str, Any]] = {
    "uv": {
        "binary": "uv",
        "path": ["cache", "dir"],
        "help": ["cache", "prune", "--help"],
        "phrase": "Prune all unreachable objects from the cache",
        "action": ["cache", "prune"],
        "source": "https://docs.astral.sh/uv/concepts/cache/",
        "effect": "removes only unused generated objects with owner-managed cache locking; required projects are not the target",
    },
    "pnpm": {
        "binary": "pnpm",
        "path": ["store", "path"],
        "help": ["store", "--help"],
        "phrase": "Removes unreferenced",
        "action": ["store", "prune"],
        "source": "https://pnpm.io/cli/store",
        "effect": "removes unreferenced package objects; no force mode or alien directory removal; project source is not targeted",
    },
    "npm": {
        "binary": "npm",
        "path": ["config", "get", "cache"],
        "help": ["cache", "--help"],
        "phrase": "npm cache verify",
        "action": ["cache", "verify"],
        "source": "https://docs.npmjs.com/cli/commands/npm-cache/",
        "effect": "verifies cache integrity and garbage-collects unneeded cache data; does not force-clean the entire cache or alter source projects",
    },
    "pip": {
        "binary": "pip3",
        "path": ["cache", "dir"],
        "help": ["cache", "--help"],
        "phrase": "- purge: Remove all items from the cache.",
        "action": ["cache", "purge"],
        "source": "https://pip.pypa.io/en/stable/cli/pip_cache/",
        "effect": "clears generated wheel/download cache items, not installed environments or source projects; cached packages will need fetching or rebuilding later",
    },
    "go": {
        "binary": "go",
        "path": ["env", "GOCACHE"],
        "help": ["help", "clean"],
        "phrase": "-cache flag causes clean to remove the entire go build cache",
        "action": ["clean", "-cache"],
        "source": "https://pkg.go.dev/cmd/go#hdr-Remove_object_files_and_cached_files",
        "effect": "clears only generated Go build-cache artifacts, not module download cache or source projects; future builds recompile necessary objects",
    },
}


def action_label(owner):
    interface = OWNER_INTERFACES.get(owner)
    return f"{owner} {' '.join(interface['action'])}" if interface else f"{owner} owner cleanup"


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
        {name: shutil.which(spec["binary"]) for name, spec in OWNER_INTERFACES.items()}
        if executables is None
        else executables
    )
    out = []
    for name, executable in executables.items():
        if not executable or name not in OWNER_INTERFACES:
            continue
        interface = OWNER_INTERFACES[name]
        path_cmd = [executable, *interface["path"]]
        help_cmd = [executable, *interface["help"]]
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
        phrase = interface["phrase"]
        normalized_help = " ".join(helptext.lower().split())
        if code or " ".join(phrase.lower().split()) not in normalized_help:
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
        argv = [executable, *interface["action"]]
        if name in ("uv", "pnpm"):
            state = (
                f"Observed operation: {name} owner-native cache/store prune without force. This is the installed storage owner's supported command, NOT whole-directory deletion. "
                "The tool's own path-discovery command identifies the exact current storage. The command selects only unused or unreferenced regenerable objects and coordinates with its owner storage locks; required projects and unique user work are not targeted. "
                f"{activity} This proposed operation targets no-longer-needed generated entries, not the entire resource. Exact removed bytes are unknown in advance; allocation is only an upper bound."
            )
        else:
            state = (
                f"Observed operation: {name} documented owner-native cache cleanup without force. This is the installed storage owner's supported command, NOT arbitrary whole-directory deletion. "
                f"The tool's own path-discovery command identifies the exact current storage. Published operation: {interface['effect']}. "
                f"{activity} This proposed operation targets owner-managed generated cache data, not unique user work. Exact removed bytes are unknown in advance; allocation is only an upper bound."
            )
        out.append(
            {
                "owner": name,
                "path": str(path),
                "argv": argv,
                "operation": "owner_prune",
                "state": state,
                "active": use,
                "contract_source": interface["source"],
                "display_action": " ".join(interface["action"]),
            }
        )
    return out
