#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export MODEL_CACHE_DIR="${MODEL_CACHE_DIR:-/models_cache}"
export PYTHONPATH="${ROOT}/scripts:${PYTHONPATH:-}"
exec python3 "${ROOT}/scripts/bootstrap_models.py"
