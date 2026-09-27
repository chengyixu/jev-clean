# ADR 0002: System Data belongs in Clean; installation includes model readiness

Accepted 2026-09-27; supersedes the manual model-setup portion of ADR 0001.

The product promise is **clean mysterious macOS System Data**, not just inspect it in Status. Clean therefore owns native accounting context, model-directed investigation of potential contributors, file review, selected cleanup, and receipts in one workflow. `B` switches investigation/review within Clean, while a persistent System Data panel stays visible. CLI and skill receive the same `system_data` object. Directory membership in Apple's category is still not inferred from size, and moving files to Trash is not called reclaimed disk space.

The standard installer is an end-to-end readiness transaction:

1. Reject root and unsupported platforms.
2. Find uv or provision pinned uv in a private environment.
3. Install the pinned app/runtime release in an isolated Python 3.12 tool environment.
4. Invoke the **newly installed executable**, not a possibly older PATH entry, with `doctor --verify-model`.
5. Provision the pinned HF checkpoint if missing/incomplete, verify the pinned manifest hash and all required inference-file sizes/SHA256 hashes, load it and execute a typed inference smoke test.
6. Declare Ready only when every step succeeded and the expected installed version reports verified model readiness. Failed download, checksum, load or inference is installation failure, not an app-only success.

Python package managers do not supply a reliable post-install hook for this transaction. We do not pretend that `uv tool install` alone downloads model weights. The official `install.py` owns the complete flow. Advanced source/wheel installs also automatically provision missing weights on first operation, preserving a no-manual-setup experience without hidden model-free fallback. Confirmed updates invoke the new executable's model-readiness check too.

The removed `model setup` command is not part of the normal UI/CLI/skill. Cold installation can download ~0.85 GB; cached operation remains local. Corrupt files fail integrity checks rather than being silently replaced. No user files are cleaned during installation or readiness tests.
