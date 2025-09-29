#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN=${PYTHON:-python3}

if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

pip install --upgrade pip >/dev/null
pip install -r "$ROOT_DIR/backend/requirements.txt"

export PYTHONPATH="$ROOT_DIR"

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 "$@"
