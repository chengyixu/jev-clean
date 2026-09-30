"""A release must install and identify the same version as its package metadata."""

import importlib.util
import tomllib
from pathlib import Path

from jev_clean.infrastructure import update

ROOT = Path(__file__).resolve().parents[1]


def test_installer_and_source_fallback_match_project_release(monkeypatch):
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    spec = importlib.util.spec_from_file_location("release_installer", ROOT / "install.py")
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    assert installer.VERSION == project["version"]

    def missing(_):
        raise update.PackageNotFoundError("jev-clean")

    monkeypatch.setattr(update, "version", missing)
    assert update.installed_version() == project["version"]


def test_frozen_lock_has_current_project_version():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    package = next(p for p in lock["package"] if p["name"] == "jev-clean")
    assert package["version"] == project["version"]
