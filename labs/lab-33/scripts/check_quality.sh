#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python}"
if [ -x "$SCRIPT_DIR/../../../.venv/Scripts/python.exe" ]; then
    PYTHON="$SCRIPT_DIR/../../../.venv/Scripts/python.exe"
elif [ -x "$SCRIPT_DIR/../../../.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/../../../.venv/bin/python"
fi

echo "1. Ruff lint"
"$PYTHON" -m ruff check app scripts

echo "2. Ruff format check"
"$PYTHON" -m ruff format --check app scripts

echo "QUALITY CHECK PASSED"
