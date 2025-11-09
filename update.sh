#!/usr/bin/env bash
#
# Update script for Sales Assistant. Syncs latest code, upgrades dependencies,
# and restarts services. Intended to run on the server.

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "[update] please run as root (sudo ./update.sh)"
  exit 1
fi

APP_USER=${APP_USER:-salesassistant}
APP_ROOT=${APP_ROOT:-/opt/sales-assistant}
APP_DIR="${APP_ROOT}/app"
SYSTEMD_SERVICE=${SYSTEMD_SERVICE:-sales-assistant}

echo "[update] 1/4 - Pulling latest code..."
sudo -u "${APP_USER}" git -C "${APP_DIR}" pull --ff-only

echo "[update] 2/4 - Upgrading Python dependencies..."
"${APP_ROOT}/.venv/bin/python" -V >/dev/null 2>&1 || {
  echo "[update] virtual environment not found at ${APP_ROOT}/.venv. Run deploy.sh first." >&2
  exit 1
}
"${APP_ROOT}/.venv/bin/pip" install --upgrade -r "${APP_DIR}/backend/requirements.txt"

echo "[update] 3/4 - Running database migrations (if any skipped) ... (SQLite auto) "

echo "[update] 4/4 - Restarting services..."
systemctl restart "${SYSTEMD_SERVICE}"
systemctl reload nginx

echo "[update] ✅ Update complete. Tail logs with: sudo journalctl -u ${SYSTEMD_SERVICE} -f"
