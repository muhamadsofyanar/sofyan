#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-https://app.ruanglegalitas.com}"
API_KEY="${API_KEY:-}"

if [ -z "$API_KEY" ]; then
  echo "Set API_KEY lebih dulu, contoh:"
  echo "API_KEY='isi-api-key-coolify' ./telegram-activate.sh"
  exit 1
fi

curl -fsS -X POST "$DOMAIN/api/telegram/setup" \
  -H "X-API-Key: $API_KEY"
echo
