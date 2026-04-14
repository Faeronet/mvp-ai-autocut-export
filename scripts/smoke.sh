#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MOCK_PIPELINE=true docker compose -f deploy/docker-compose.yml up -d postgres redis
sleep 3
export POSTGRES_DSN="postgres://drawdigit:drawdigit@localhost:5432/drawdigit?sslmode=disable"
export REDIS_ADDR="localhost:6379"
export DATA_DIR="$ROOT/data"
export MOCK_PIPELINE=true
go run ./cmd/api &
APIPID=$!
sleep 1
curl -sf "http://localhost:8080/healthz" >/dev/null
kill $APIPID
docker compose -f deploy/docker-compose.yml down
