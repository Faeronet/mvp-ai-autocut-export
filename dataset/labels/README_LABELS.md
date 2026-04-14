# Labels added to dataset

This label pack contains **high-quality image-level labels** for every file in the dataset.

What is included:
- `labels/json/...` — rich per-file sidecar JSON labels
- `labels/yolo_cls/...` — one-class-per-file labels for image classification style training
- `labels/classes.txt` — class list
- `labels/dataset.yaml` — simple classifier dataset descriptor
- `labels/dataset_labels.csv` — flat manifest for filtering and split logic
- `labels/review_queue.csv` — files that still require manual review for object-level or CAD-level annotation

Important:
These labels are strong for **dataset curation/classification/difficulty sampling**, but they are **not** pixel-perfect object labels.
For truly ideal training of layout detection, symbol detection, table cells, or CAD primitive extraction, manual bbox/polygon review in CVAT/Label Studio is still required.
