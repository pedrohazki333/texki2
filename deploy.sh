#!/usr/bin/env bash
# Deploy manual e reproduzível (design doc, Seção 9).
# Pré-requisito: `.env` preenchido no servidor.
# Uso: ./deploy.sh
set -euo pipefail

cd "$(dirname "$0")"

git pull
docker compose build
docker compose up -d
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -m app.db.seed
