# Remote Training: YOLOv8 Layout

This project is trained on another server. Use this guide to run layout training remotely.

## 1) Server requirements

- Ubuntu 22.04+
- NVIDIA driver + CUDA runtime available
- Python 3.10+
- 1 GPU (recommended: 12+ GB VRAM for `imgsz=1280`, batch 4)

## 2) Prepare environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install ultralytics==8.3.0
```

If needed, install torch with CUDA according to your server stack.

## 3) Dataset assumptions

Script reads images from:

- `dataset/mix`
- `dataset/worst`
- `dataset/handwritten`
- `dataset/dense_dims`

and expects YOLO labels in a separate folder (`--labels-root`) with same basename:

- image: `user_orig_001_MDS00448.jpg`
- label: `<labels-root>/user_orig_001_MDS00448.txt`

Label format is standard YOLO detection:

`<class_id> <x_center> <y_center> <width> <height>`

## 4) Run training

From repo root:

```bash
python3 scripts/train_layout_yolo.py \
  --repo-root . \
  --images-root dataset \
  --labels-root /data/layout_labels_yolo \
  --convert-cls-labels \
  --out-root training/layout \
  --epochs 100 \
  --imgsz 1280 \
  --batch 4 \
  --device 0 \
  --model yolov8n.pt \
  --project training/layout/runs \
  --name layout_yolov8n_baseline
```

## 5) Outputs

- Prepared split dataset: `training/layout/prepared_dataset`
- Dataset yaml: `training/layout/prepared_dataset/dataset.yaml`
- Training run artifacts: `training/layout/runs/layout_yolov8n_baseline`
  - `weights/best.pt`
  - `weights/last.pt`
  - metrics plots and logs

If your labels are in cls-only format (`<class_id>` one per line), use `--convert-cls-labels`.
The script will convert such lines to full-image boxes (`cls 0.5 0.5 1.0 1.0`) to unblock baseline training.

## 6) Recommended first run profile

- `imgsz=1280`
- `batch=2..4` (adjust for VRAM)
- `epochs=80..120`
- `workers=4`

For low VRAM cards, start with `imgsz=1024`, `batch=2`.

