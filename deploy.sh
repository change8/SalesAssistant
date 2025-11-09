#!/usr/bin/env bash
#
# One-click deployment script for Sales Assistant on CentOS/TencentOS.
# Usage:
#   sudo SA_DOMAIN=saleassisstant.chat SA_ADMIN_EMAIL=you@example.com ./deploy.sh

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "[deploy] please run as root (sudo ./deploy.sh)"
  exit 1
fi

APP_USER=${APP_USER:-salesassistant}
APP_GROUP=${APP_GROUP:-${APP_USER}}
APP_ROOT=${APP_ROOT:-/opt/sales-assistant}
APP_DIR="${APP_ROOT}/app"
REPO_URL=${REPO_URL:-https://github.com/change8/SalesAssistant.git}
PYTHON_BIN=${PYTHON_BIN:-python3}
DOMAIN=${SA_DOMAIN:-saleassisstant.chat}
DOMAIN_WWW="www.${DOMAIN}"
ADMIN_EMAIL=${SA_ADMIN_EMAIL:-}
SYSTEMD_UNIT_PATH=/etc/systemd/system/sales-assistant.service
NGINX_CONF_PATH=/etc/nginx/conf.d/sales-assistant.conf

if [[ -z "${ADMIN_EMAIL}" ]]; then
  echo "[deploy] SA_ADMIN_EMAIL is required so Certbot can register the certificate."
  echo "Example: sudo SA_ADMIN_EMAIL=you@example.com ./deploy.sh"
  exit 1
fi

echo "[deploy] 1/9 - Updating package index and installing base dependencies..."
if command -v dnf >/dev/null 2>&1; then
  PKG_MGR=dnf
else
  PKG_MGR=yum
fi

${PKG_MGR} -y update
if ${PKG_MGR} install -y epel-release >/dev/null 2>&1; then
  echo "[deploy] epel-release installed."
else
  echo "[deploy] (warning) epel-release not available for this OS, continuing without it."
fi

REQUIRED_PACKAGES=(
  git
  "${PYTHON_BIN}"
  "${PYTHON_BIN}-devel"
  gcc
  nginx
  certbot
  python3-certbot-nginx
  firewalld
)
OPTIONAL_PACKAGES=(
  python3-venv
)

for pkg in "${REQUIRED_PACKAGES[@]}"; do
  if ! ${PKG_MGR} install -y "${pkg}"; then
    echo "[deploy] failed to install required package ${pkg}. Please resolve manually."
    exit 1
  fi
done

for pkg in "${OPTIONAL_PACKAGES[@]}"; do
  ${PKG_MGR} install -y "${pkg}" || echo "[deploy] (warning) optional package ${pkg} not available."
done

echo "[deploy] 2/9 - Ensuring application system user ${APP_USER} exists..."
if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --shell /sbin/nologin "${APP_USER}"
fi

mkdir -p "${APP_ROOT}"
chown "${APP_USER}:${APP_GROUP}" "${APP_ROOT}"

if [[ ! -d "${APP_DIR}/.git" ]]; then
  echo "[deploy] 3/9 - Cloning repository..."
  sudo -u "${APP_USER}" git clone --depth=1 "${REPO_URL}" "${APP_DIR}"
else
  echo "[deploy] 3/9 - Repository already exists, pulling latest code..."
  sudo -u "${APP_USER}" git -C "${APP_DIR}" pull --ff-only
fi

echo "[deploy] 4/9 - Creating Python virtual environment..."
PY_VERSION="$(${PYTHON_BIN} -V | awk '{print $2}')"
PY_MAJOR=$(echo "${PY_VERSION}" | cut -d. -f1)
PY_MINOR=$(echo "${PY_VERSION}" | cut -d. -f2)
if (( PY_MAJOR < 3 || (PY_MAJOR == 3 && PY_MINOR < 10) )); then
  echo "[deploy] detected ${PYTHON_BIN} version ${PY_VERSION}. Python 3.10+ required."
  echo "[deploy] install a newer python (e.g. via https://github.com/pyenv/pyenv-installer) and set PYTHON_BIN=/usr/local/bin/python3.11"
  exit 1
fi

if [[ ! -d "${APP_ROOT}/.venv" ]]; then
  sudo -u "${APP_USER}" "${PYTHON_BIN}" -m venv "${APP_ROOT}/.venv"
fi
"${APP_ROOT}/.venv/bin/pip" install --upgrade pip setuptools wheel
"${APP_ROOT}/.venv/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"

if [[ ! -f "${APP_ROOT}/.env" ]]; then
  echo "[deploy] 5/9 - No /opt/sales-assistant/.env found. Copying template..."
  sudo -u "${APP_USER}" cp "${APP_DIR}/.env.example" "${APP_ROOT}/.env"
  echo "[deploy] *** IMPORTANT: update /opt/sales-assistant/.env with production secrets before starting the service ***"
fi
chown "${APP_USER}:${APP_GROUP}" "${APP_ROOT}/.env"

echo "[deploy] 6/9 - Installing systemd service..."
sudo -u "${APP_USER}" mkdir -p "${APP_ROOT}/logs"
cp "${APP_DIR}/ops/systemd/sales-assistant.service" "${SYSTEMD_UNIT_PATH}"
sed -i "s#__APP_ROOT__#${APP_ROOT}#g" "${SYSTEMD_UNIT_PATH}"
sed -i "s#__APP_USER__#${APP_USER}#g" "${SYSTEMD_UNIT_PATH}"
systemctl daemon-reload

if systemctl is-enabled sales-assistant >/dev/null 2>&1; then
  systemctl restart sales-assistant
else
  systemctl enable --now sales-assistant
fi

echo "[deploy] 7/9 - Configuring nginx reverse proxy..."
cp "${APP_DIR}/ops/nginx/sales-assistant.template.conf" "${NGINX_CONF_PATH}"
sed -i "s#__DOMAIN__#${DOMAIN}#g" "${NGINX_CONF_PATH}"
sed -i "s#__DOMAIN_WWW__#${DOMAIN_WWW}#g" "${NGINX_CONF_PATH}"
sed -i "s#__APP_PORT__#8000#g" "${NGINX_CONF_PATH}"
nginx -t
systemctl enable --now nginx
systemctl reload nginx

echo "[deploy] 8/9 - Opening firewall for HTTP/HTTPS..."
systemctl enable --now firewalld
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

echo "[deploy] 9/9 - Issuing/renewing Let's Encrypt certificate..."
if ! certbot certificates --quiet --max-log-backups 0 --domains "${DOMAIN}" >/dev/null 2>&1; then
  certbot --nginx --non-interactive --agree-tos --redirect \
    --email "${ADMIN_EMAIL}" \
    -d "${DOMAIN}" -d "${DOMAIN_WWW}"
else
  certbot renew --quiet
fi

systemctl reload nginx

cat <<'EOF'
[deploy] ✅ Deployment complete.

Next steps:
1. Edit /opt/sales-assistant/.env with production secrets (API keys, database URL, etc.).
2. Restart the application if you changed .env: sudo systemctl restart sales-assistant
3. Verify service status:
     sudo systemctl status sales-assistant
     sudo journalctl -u sales-assistant -n 100 --no-pager
4. Application should now be reachable at: https://DOMAIN/
EOF
