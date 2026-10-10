"""Reobserved fixed owner-native operations; never commands from a plan/model."""

import os
import subprocess
from pathlib import Path

from jev_clean.infrastructure import owner_tools
from jev_clean.infrastructure.scanner import fingerprint, no_symlink_ancestors


def prune_selected(item, *, runner=subprocess.run):
    if os.geteuid() == 0:
        raise ValueError("Never execute cleanup as root")
    if item.operation != "owner_prune" or item.owner_tool not in ("uv", "pnpm"):
        raise ValueError("Unsupported owner operation")
    observation = next(
        (
            r
            for r in owner_tools.owner_observations()
            if r["owner"] == item.owner_tool and r["path"] == item.path
        ),
        None,
    )
    if observation is None:
        raise ValueError("Owner tool/path contract changed or unavailable")
    if observation["active"] is not False:
        raise ValueError("Owner active use unknown or active; retry when idle")
    path = Path(item.path)
    if not no_symlink_ancestors(path) or fingerprint(path.lstat()) != item.fingerprint:
        raise ValueError("Owner cache identity changed")
    # argv comes ONLY from fresh installed owner discovery; never item evidence.
    result = runner(
        observation["argv"],
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "COREPACK_ENABLE_NETWORK": "0", "COREPACK_ENABLE_DOWNLOAD_PROMPT": "0"},
    )
    return {
        "owner": item.owner_tool,
        "path": item.path,
        "operation": "owner_prune",
        "complete": result.returncode == 0,
        "returncode": result.returncode,
        "reversible": False,
        "stdout": result.stdout[-4096:],
        "stderr": result.stderr[-4096:],
    }
