#!/usr/bin/env bash
set -euo pipefail

echo "== Sofyan OS installer =="

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker belum tersedia. Install Docker dulu, lalu jalankan ulang script ini."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin belum tersedia."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "File .env dibuat."
  echo "Edit password dan secret dulu:"
  echo "  nano .env"
  echo
  echo "Setelah selesai, jalankan lagi:"
  echo "  ./install.sh"
  exit 0
fi

docker compose up -d --build

echo
echo "Sofyan OS aktif di http://127.0.0.1:8088"
echo "Health check:"
curl -fsS http://127.0.0.1:8088/api/health || true
echo
echo
echo "Untuk domain app.ruanglegalitas.com:"
echo "1. Pastikan DNS A record menuju IP VPS."
echo "2. Pasang file deploy/nginx-app.ruanglegalitas.com.conf ke Nginx."
echo "3. Aktifkan HTTPS dengan Certbot bila Nginx Anda menggunakannya."
