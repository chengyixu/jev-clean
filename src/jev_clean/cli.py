"""Human CLI and noninteractive agent API; cleanup is never implicit."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from jev_clean.application.service import audit, load_plan, reassess_selection, save_plan
from jev_clean.infrastructure import native
from jev_clean.infrastructure.model import MODEL_ID, MODEL_REVISION, local_snapshot
from jev_clean.infrastructure.trash import TrashStore
from jev_clean.infrastructure.update import check_update, installed_version


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="jev-clean · Nexora — evidence-first macOS System Data review")
    p.add_argument("--version", action="version", version=installed_version())
    sub = p.add_subparsers(dest="command")
    for name in ["clean", "status", "tui"]:
        cmd = sub.add_parser(name, help=f"{name.title()} (read-only unless explicitly confirmed)")
        cmd.add_argument(
            "--demo",
            action="store_true",
            help="Synthetic file metadata with REAL mandatory model inference; no removal",
        )
        cmd.add_argument("--json", action="store_true", help="Private JSON, no interactive sudo prompts")
        cmd.add_argument(
            "--deep",
            action="store_true",
            help="Native sudo diagnostics; authenticate in terminal first for JSON",
        )
        cmd.add_argument(
            "--root",
            action="append",
            type=Path,
            help="Narrow model exploration to this read-only root (repeatable, JSON only)",
        )
        cmd.add_argument("--output", type=Path, help="Save a private JSON plan (valid for one hour)")
    cmd = sub.add_parser("apply", help="Stage explicitly selected plan files in Trash, revalidating each")
    cmd.add_argument("plan", type=Path)
    cmd.add_argument(
        "--ids", required=True, help="Comma-separated IDs from the reviewed JSON plan; no wildcard/all"
    )
    cmd.add_argument("--confirm", help="For agents after explicit human authorization: literal TRASH")
    sub.add_parser("history", help="JSON transaction history")
    cmd = sub.add_parser("restore", help="Restore a batch without overwriting source files")
    cmd.add_argument("batch")
    cmd.add_argument("--confirm", help="For agents after explicit human authorization: literal RESTORE")
    cmd = sub.add_parser("model", help="Explicit model setup/status")
    cmd.add_argument("action", choices=["setup", "status"])
    cmd = sub.add_parser("update", help="Check public GitHub releases; explicit confirmation to install")
    cmd.add_argument("--apply", action="store_true")
    cmd = sub.add_parser("completion", help="Print completion script; does not edit shell config")
    cmd.add_argument("shell", choices=["bash", "zsh", "fish"])
    sub.add_parser("doctor", help="Read-only compatibility and permission diagnostics")
    return p


def confirm(word: str, supplied: str | None) -> None:
    if supplied == word:
        return
    if supplied is not None or not sys.stdin.isatty():
        raise ValueError(f"Explicit human authorization required: --confirm {word}")
    if input(f"Type {word} to confirm: ").strip() != word:
        raise ValueError("Cancelled")


def emit(value) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    home = Path.home()
    try:
        if os.geteuid() == 0:
            raise ValueError(
                "Run jev-clean as your normal user. It requests sudo only for read-only diagnostics."
            )
        if args.command in (None, "tui", "clean", "status"):
            demo = getattr(args, "demo", False)
            json_mode = getattr(args, "json", False) or not sys.stdout.isatty()
            mode = args.command if args.command not in (None, "tui") else "status"
            if platform.system() != "Darwin" and not demo:
                raise ValueError("macOS required for real scans. Use --demo for a portable preview.")
            if json_mode:
                if getattr(args, "deep", False):
                    code, _, _ = native.run(["/usr/bin/sudo", "-n", "-v"], 3)
                    if code:
                        raise ValueError(
                            "Deep JSON needs prior terminal authentication: sudo -v. Passwords are never accepted here."
                        )
                report = audit(
                    home,
                    mode,
                    demo=demo,
                    roots=getattr(args, "root", None),
                    deep=getattr(args, "deep", False),
                    progress=lambda text: print(text, file=sys.stderr),
                )
                if getattr(args, "output", None):
                    save_plan(args.output.absolute(), report)
                emit(report.to_dict())
            else:
                from jev_clean.ui.app import JevCleanApp

                JevCleanApp(
                    home=home,
                    demo=demo,
                    initial=None if args.command in (None, "tui") else mode,
                ).run()
        elif args.command == "apply":
            items = load_plan(args.plan.absolute(), home)
            ids = set(args.ids.split(","))
            known = {i.id for i in items}
            if not ids or not ids <= known:
                raise ValueError("Unknown or empty selected IDs")
            selected = [i for i in items if i.id in ids]
            if not all(i.selectable for i in selected):
                raise ValueError("Selection includes protected files; rescan/review")
            print(
                f"Stage {len(selected)} selected files in Trash. This does not free space.", file=sys.stderr
            )
            for item in selected:
                print(item.path, file=sys.stderr)
            confirm("TRASH", args.confirm)
            assessed = reassess_selection(selected)
            result = TrashStore(home).move(assessed, open_paths=native.open_files())
            emit(asdict(result))
            return 1 if result.failed else 0
        elif args.command == "history":
            emit(TrashStore(home).history())
        elif args.command == "restore":
            confirm("RESTORE", args.confirm)
            result = TrashStore(home).restore(args.batch)
            emit(asdict(result))
            return 1 if result.failed else 0
        elif args.command == "doctor":
            emit(
                {
                    "version": installed_version(),
                    "platform": platform.system(),
                    "arch": platform.machine(),
                    "root": False,
                    "sudo_cached": native.run(["/usr/bin/sudo", "-n", "-v"], 3)[0] == 0,
                    "lsof_available": native.open_files() is not None,
                    "note": "sudo does not bypass Full Disk Access/TCC. No file changes performed.",
                }
            )
        elif args.command == "model":
            path = local_snapshot(download=args.action == "setup")
            emit({"model": MODEL_ID, "revision": MODEL_REVISION, "snapshot": str(path), "inference": "local"})
        elif args.command == "update":
            info = check_update()
            emit(info)
            if args.apply:
                if not sys.stdin.isatty():
                    raise ValueError("Update installation requires interactive terminal confirmation")
                print(
                    f"Install reviewed public release from {info['url']} using uv tool install. The mandatory model runtime is included on arm64."
                )
                confirm("UPDATE", None)
                uv = shutil.which("uv")
                if not uv:
                    raise ValueError("uv is required; install uv separately from its official distribution")
                spec = info["install_spec"]
                return subprocess.run([uv, "tool", "install", "--force", spec], check=False).returncode
        elif args.command == "completion":
            words = "clean status tui apply restore history model update doctor completion"
            if args.shell == "bash":
                print(f"complete -W '{words}' jev-clean")
            elif args.shell == "zsh":
                print(f"#compdef jev-clean\n_arguments '1:command:({words})'")
            else:
                print(f"complete -c jev-clean -f -a '{words}'")
        return 0
    except KeyboardInterrupt:
        print("Cancelled.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"jev-clean: {error}", file=sys.stderr)
        return 1
