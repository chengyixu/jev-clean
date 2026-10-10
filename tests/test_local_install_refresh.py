import json
import subprocess

from test_turnkey_install import installer


def test_source_preview_rebuilds_package_even_when_version_is_unchanged(tmp_path):
    module = installer()
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        if argv[1:3] == ["tool", "dir"]:
            return subprocess.CompletedProcess(argv, 0, stdout=str(tmp_path) + "\n")
        proof = {
            "version": module.VERSION,
            "model": {
                "ready": True,
                "weights_verified": True,
                "revision": "fixture",
                "model": "fixture",
                "smoke_inference_ms": 1.0,
            },
        }
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(proof))

    module.install("uv", source="/local/verified-checkout", runner=run)
    assert "--reinstall-package" in calls[0]
    index = calls[0].index("--reinstall-package")
    assert calls[0][index + 1] == "jev-clean"
