#!/usr/bin/env bash
# Infinity HRMS — idempotent redeploy / refresh.
#
# Two modes:
#   ./deploy/redeploy.sh           # safe — pulls + rebuilds + restarts, preserves DB
#   ./deploy/redeploy.sh --wipe    # destructive — drops volumes, fresh DB, re-seeds
#
# Run from /opt/infinity-hrms on the VPS.

set -euo pipefail

cd "$(dirname "$0")/.."

WIPE=0
SEED=0
for arg in "$@"; do
  case "$arg" in
    --wipe) WIPE=1; SEED=1 ;;
    --seed) SEED=1 ;;
    *) echo "Unknown flag: $arg"; exit 1 ;;
  esac
done

if [[ ! -f .env ]]; then
  echo "✗ .env missing. Run deploy/setup.sh first."; exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

echo "→ Fast-forward pull"
git pull --ff-only

if [[ $WIPE -eq 1 ]]; then
  echo "⚠  --wipe: destroying volumes (DB, sites, redis, caddy state)"
  $COMPOSE down -v
fi

echo "→ Rebuilding image"
$COMPOSE build

echo "→ Bringing stack up"
$COMPOSE up -d

echo "→ Waiting for backend to be healthy"
for i in {1..60}; do
  if $COMPOSE exec -T backend bench --site "$DOMAIN" version >/dev/null 2>&1; then
    echo "✓ backend up"
    break
  fi
  sleep 5
done

echo "→ Running migrations"
$COMPOSE exec -T backend bench --site "$DOMAIN" migrate

if [[ $SEED -eq 1 ]]; then
  echo "→ Seeding India payroll demo data"
  $COMPOSE exec -T backend bench --site "$DOMAIN" execute infinity_hrms.seed.run_all || true
fi

echo
echo "✓ Redeploy complete. https://${DOMAIN}"
