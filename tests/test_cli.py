import json
import os
import subprocess
import sys
from pathlib import Path

from jev_clean.cli import main

ROOT = Path(__file__).resolve().parents[1]


def cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "jev_clean", *args],
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        timeout=20,
    )


def test_cli_demo_uses_neural_boundary_and_labels_metadata(neural_boundary, capsys):
    assert main(["clean", "--demo", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["demo"] and report["exploration"]["steps"]
    assert report["scan"]["candidates"][0]["decision"]["backend"] == "test neural boundary"
    assert all(not c["eligible"] for c in report["scan"]["candidates"] if c["kind"] == "database")


def test_cli_no_model_off_or_removed_modes():
    for args in [("clean", "--model", "off"), ("analyze",), ("optimize",), ("model", "setup")]:
        assert cli(*args).returncode != 0


def test_cli_help_and_completion():
    assert cli("--help").returncode == 0
    assert cli("--version").stdout.strip() == "0.1.2"
    for shell in ["bash", "zsh", "fish"]:
        result = cli("completion", shell)
        assert result.returncode == 0 and "jev-clean" in result.stdout
        assert "analyze" not in result.stdout and "optimize" not in result.stdout


def test_apply_requires_selection():
    result = cli("apply", "missing.json")
    assert result.returncode != 0 and "ids" in result.stderr
