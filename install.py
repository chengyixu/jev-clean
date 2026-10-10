#!/usr/bin/env python3
"""Turnkey installer. App + pinned model + real inference, or installation fails.

Run without sudo. Uses Python's stdlib and installs uv into a private venv if needed.
No pip post-install hook, curl-to-shell, password capture or model-free success path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "0.4.0.dev4"
ADAPTER_ID = "jev-cleanup-laya-file-resources-v2"
ADAPTER_SHA256 = "5200fad503588937a20cb78094c8c8731ef35dc8f2ce9c973b860c33c9719a38"
REPO = "https://github.com/chengyixu/jev-clean"


def install(uv: str, *, runner=subprocess.run, source: str | None = None) -> dict:
    package = source or f"jev-clean @ git+{REPO}.git@v{VERSION}"
    print(f"1/3 Installing jev-clean {VERSION} and its mandatory model runtime…", flush=True)
    command = [uv, "tool", "install", "--force", "--python", "3.12"]
    if source:
        command += ["--reinstall-package", "jev-clean"]
    runner([*command, package], check=True)
    tool_dir = runner([uv, "tool", "dir"], check=True, text=True, capture_output=True).stdout.strip()
    executable = Path(tool_dir) / "jev-clean/bin/jev-clean"
    print(
        "2/3 Provisioning and checksum-verifying the pinned local model (~0.85 GB on first install)…",
        flush=True,
    )
    print("3/3 Running real inference before declaring the installation ready…", flush=True)
    result = runner(
        [str(executable), "doctor", "--verify-model"], check=True, text=True, stdout=subprocess.PIPE
    )
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    status = json.loads(result.stdout)
    proof = status.get("model", {})
    if (
        status.get("version") != VERSION
        or proof.get("ready") is not True
        or proof.get("weights_verified") is not True
        or not proof.get("revision")
        or not proof.get("model")
        or not isinstance(proof.get("smoke_inference_ms"), (int, float))
    ):
        raise RuntimeError("Installed model did not pass readiness verification. Installation is incomplete.")
    return {"ready": True, "version": VERSION, "model": proof, "executable": str(executable)}


def ensure_uv() -> str:
    found = shutil.which("uv")
    if found:
        return found
    bootstrap = Path.home() / ".local/share/jev-clean/installer"
    bootstrap.parent.mkdir(parents=True, exist_ok=True)
    if bootstrap.is_symlink():
        raise RuntimeError("Refusing symlink installer environment")
    print("Installing pinned uv into a private bootstrap environment (no sudo)…", flush=True)
    subprocess.run([sys.executable, "-m", "venv", str(bootstrap)], check=True)
    python = bootstrap / "bin/python"
    subprocess.run(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check", "uv==0.9.27"], check=True
    )
    return str(bootstrap / "bin/uv")


def provision_adapter(source: Path | None) -> Path:
    target = Path.home() / ".local/share/jev-clean/models" / ADAPTER_ID / "model.safetensors"
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError("Refusing symlink model installation path")
    if source is None:
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != ADAPTER_SHA256:
            raise ValueError("This local preview requires --adapter with the verified learned Laya weights")
        return target
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != ADAPTER_SHA256:
        raise ValueError("Learned adapter checksum mismatch; installation stopped")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".learned-", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def main() -> int:
    p = argparse.ArgumentParser(description="Install jev-clean with a ready-to-use local model")
    p.add_argument(
        "--source",
        type=Path,
        help="Developer verification only: install this local checkout instead of the pinned release",
    )
    p.add_argument(
        "--adapter", type=Path, help="Local verified learned Laya adapter for this preview; SHA256 is pinned"
    )
    args = p.parse_args()
    if os.geteuid() == 0:
        p.error("Do not run this installer with sudo/root")
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        p.error("Apple Silicon macOS is required for mandatory local model inference")
    source = None
    if args.source:
        source = str(args.source.resolve(strict=True))
        if not (Path(source) / "pyproject.toml").is_file():
            p.error("--source must be a local jev-clean checkout")
    try:
        provision_adapter(args.adapter)
        result = install(ensure_uv(), source=source)
    except (Exception, KeyboardInterrupt) as error:
        print(
            f"Installation incomplete: {error}\nNo ready state claimed. Re-run the installer to resume.",
            file=sys.stderr,
        )
        return 1
    print(f"\nReady: jev-clean {result['version']} + verified local model. No setup command needed.")
    print(f"Launch: {result['executable']}\nOr run jev-clean if your uv executable directory is on PATH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
