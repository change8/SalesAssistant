#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$PROJECT_ROOT/../.env" ]; then
  set -o allexport
  source "$PROJECT_ROOT/../.env"
  set +o allexport
fi

cd "$PROJECT_ROOT"

PYTHON_INTERPRETER="${PYTHON_INTERPRETER:-}"
if [ -z "${PYTHON_INTERPRETER}" ]; then
  for candidate in python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_INTERPRETER="$candidate"
      break
    fi
  done
fi

if [ -z "${PYTHON_INTERPRETER}" ]; then
  echo "未找到可用的 Python 3.10+ 解释器，请先安装 python3.11 (推荐 brew install python@3.11)。" >&2
  exit 1
fi

RECREATE_VENV=false
VENV_VERSION=""
if [ -d "$PROJECT_ROOT/.venv" ]; then
  VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
  if [ ! -x "$VENV_PYTHON" ]; then
    RECREATE_VENV=true
  else
    if ! "$VENV_PYTHON" -c 'import sys; major, minor = sys.version_info[:2]; sys.exit(0 if (major == 3 and (10 <= minor <= 12)) else 1)'; then
      DETECTED_VERSION=$($VENV_PYTHON -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
      echo "检测到虚拟环境使用的 Python 版本为 ${DETECTED_VERSION:-unknown}，将使用 $PYTHON_INTERPRETER 重新创建。"
      RECREATE_VENV=true
    fi
  fi
else
  RECREATE_VENV=true
fi

if [ "$RECREATE_VENV" = true ]; then
  rm -rf "$PROJECT_ROOT/.venv"
  echo "使用 $PYTHON_INTERPRETER 创建虚拟环境..."
  "$PYTHON_INTERPRETER" -m venv "$PROJECT_ROOT/.venv"
fi

source "$PROJECT_ROOT/.venv/bin/activate"

export PYTHONPATH="$PROJECT_ROOT"

python -m pip install --upgrade pip >/dev/null
python -m pip install -r "$PROJECT_ROOT/requirements.txt"

uvicorn app.main:app --host 0.0.0.0 --port 8000
