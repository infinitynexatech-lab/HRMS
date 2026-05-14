#!/usr/bin/env bash
# Infinity HRMS — one-shot Hetzner VPS bootstrap.
#
# What it does:
#   1. Installs Docker + UFW
#   2. Configures firewall (SSH/HTTP/HTTPS only)
#   3. Clones (or fast-forwards) this repo into /opt/infinity-hrms
#   4. Generates strong secrets on first run, writes .env
#   5. Builds the custom image and brings up the production stack
#
# Run on a fresh Ubuntu 24.04 VPS:
#   curl -fsSL https://raw.githubusercontent.com/infinitynexatech-lab/HRMS/main/deploy/setup.sh \
#     | sudo REPO_URL=https://github.com/infinitynexatech-lab/HRMS DOMAIN=hrms.infinitynexatech.com bash

set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/infinity-hrms}"
DOMAIN="${DOMAIN:-hrms.infinitynexatech.com}"
REPO_URL="${REPO_URL:-https://github.com/infinitynexatech-lab/HRMS}"

if [[ $EUID -ne 0 ]]; then
  echo "✗ Run as root (use sudo)."; exit 1
fi

echo "→ Updating apt cache + installing prerequisites"
apt-get update -qq
apt-get install -y -qq curl git openssl ufw ca-certificates

if ! command -v docker >/dev/null; then
  echo "→ Installing Docker"
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

echo "→ Configuring firewall (SSH/HTTP/HTTPS only)"
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "→ Cloning repo to ${INSTALL_DIR}"
if [[ ! -d "$INSTALL_DIR/.git" ]]; then
  git clone "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"
git pull --ff-only

if [[ ! -f .env ]]; then
  echo "→ Generating .env (will not overwrite if present)"
  cat > .env <<EOF
DOMAIN=${DOMAIN}
SITE_NAME=${DOMAIN}
MARIADB_ROOT_PASSWORD=$(openssl rand -hex 24)
DB_PASSWORD=$(openssl rand -hex 24)
ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)
ENCRYPTION_KEY=$(openssl rand -hex 32)
FRAPPE_VERSION=version-15
ERPNEXT_VERSION=version-15
HRMS_VERSION=version-15
IMAGE_TAG=v1.0.0
IMAGE=infinity-hrms:v1.0.0
EOF
  chmod 600 .env
  echo "✓ .env written. Admin password:"
  echo "    $(grep ADMIN_PASSWORD .env | cut -d= -f2)"
  echo "  (saved — keep this VPS secured)"
fi

echo "→ Building custom image (~5–8 min on CPX22)"
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

echo "→ Starting production stack"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo
echo "✓ Stack starting. Track progress with:"
echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f create-site backend"
echo
echo "First-boot site creation takes ~3–5 minutes. When ready, open"
echo "  https://${DOMAIN}"
echo "and sign in as Administrator with the password printed above."
