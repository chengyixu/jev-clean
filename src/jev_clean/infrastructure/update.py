"""Explicit upstream release checks; no curl-to-shell or silent self updates."""

import json
import re
import urllib.request
from importlib.metadata import PackageNotFoundError, version

from packaging.version import Version

REPO = "https://github.com/chengyixu/jev-clean"


def installed_version() -> str:
    try:
        return version("jev-clean")
    except PackageNotFoundError:
        return "0.1.3"


def latest_version(data: dict) -> str:
    tag = data.get("tag_name", "")
    if not re.fullmatch(r"v\d+\.\d+\.\d+(?:[a-zA-Z0-9.-]*)?", tag):
        raise ValueError("Invalid release tag")
    if data.get("html_url") != f"{REPO}/releases/tag/{tag}":
        raise ValueError("Untrusted release identity")
    Version(tag[1:])
    return tag[1:]


def check_update() -> dict:
    request = urllib.request.Request(
        "https://api.github.com/repos/chengyixu/jev-clean/releases/latest",
        headers={"User-Agent": "jev-clean", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        data = json.load(response)
    latest = latest_version(data)
    return {
        "installed": installed_version(),
        "latest": latest,
        "available": Version(latest) > Version(installed_version()),
        "url": data["html_url"],
        "install_spec": f"jev-clean @ git+{REPO}.git@v{latest}",
    }
