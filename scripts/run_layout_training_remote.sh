#!/usr/bin/env bash
set -euo pipefail

# Remote training launcher for mcp_mvp layout model.
# Usage:
#   bash scripts/run_layout_training_remote.sh
# Optional overrides via env:
#   PYTHON_BIN=python3.10
#   LABELS_ROOT=/data/layout_labels_yolo
#   EPOCHS=120 IMGSZ=1280 BATCH=4 DEVICE=0 MODEL=yolov8n.pt

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv-train}"

LABELS_ROOT="${LABELS_ROOT:-training/layout/prepared_dataset/labels}"
IMAGES_ROOT="${IMAGES_ROOT:-training/layout/prepared_dataset/images}"
OUT_ROOT="${OUT_ROOT:-training/layout}"
PROJECT_DIR="${PROJECT_DIR:-training/layout/runs}"
RUN_NAME="${RUN_NAME:-layout_yolov8n_baseline}"

EPOCHS="${EPOCHS:-100}"
IMGSZ="${IMGSZ:-1280}"
BATCH="${BATCH:-4}"
DEVICE="${DEVICE:-0}"
MODEL="${MODEL:-yolov8n.pt}"
WORKERS="${WORKERS:-4}"
SEED="${SEED:-42}"

echo "[train] repo root: $REPO_ROOT"
echo "[train] python: $PYTHON_BIN"
echo "[train] venv: $VENV_DIR"

"$PYTHON_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel
python -m pip install "ultralytics==8.3.0"

if command -v nvidia-smi >/dev/null 2>&1; then
  echo "[train] GPU detected:"
  nvidia-smi || true
else
  echo "[train] WARNING: nvidia-smi not found. Training may run on CPU."
fi

if [[ ! -d "$LABELS_ROOT" ]]; then
  echo "[train] ERROR: labels root not found: $LABELS_ROOT" >&2
  exit 1
fi

if [[ ! -d "$IMAGES_ROOT" ]]; then
  echo "[train] ERROR: images root not found: $IMAGES_ROOT" >&2
  exit 1
fi

echo "[train] starting YOLO layout training..."
python scripts/train_layout_yolo.py \
  --repo-root . \
  --images-root "$IMAGES_ROOT" \
  --labels-root "$LABELS_ROOT" \
  --convert-cls-labels \
  --out-root "$OUT_ROOT" \
  --epochs "$EPOCHS" \
  --imgsz "$IMGSZ" \
  --batch "$BATCH" \
  --device "$DEVICE" \
  --model "$MODEL" \
  --workers "$WORKERS" \
  --seed "$SEED" \
  --project "$PROJECT_DIR" \
  --name "$RUN_NAME" \
  "$@"

echo "[train] done. Artifacts: $PROJECT_DIR/$RUN_NAME"
