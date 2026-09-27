#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python -m ruff check src tests scripts install.py
python -m ruff format --check src tests scripts install.py
python -m mypy src
python -m pytest --cov=jev_clean --cov-report=term-missing --cov-fail-under=75
bash scripts/repo-guards.sh
