# Model management (MVP)

## Automatically installed on first `docker compose up`

These weights are downloaded into the Docker volume `models_cache` (mounted at `/models_cache` in services) by the **`bootstrap-models`** one-shot container (`scripts/bootstrap_models.py`):

| Model | Role |
|-------|------|
| PaddleOCR **PP-OCRv4** det | Text detection |
| PaddleOCR **PP-OCRv4** rec | Text recognition |
| PaddleOCR **PP-OCRv4** cls | Text direction / angle |
| Paddle **PP-Structure** table backend (SLANet-class) | Table structure / cells |
| **YOLOv8n** baseline (`yolov8n.pt` saved as `layout/yolov8n_layout.pt`) | Layout / zoning (with rule-based label fusion) |

Status file: `/models_cache/bootstrap_status.json` (written by bootstrap).

## Not downloaded by default

| Item | Notes |
|------|------|
| EfficientNet-B0 / ResNet18 sheet classifier | `ENABLE_MODEL_SHEET_CLASSIFIER=false` |
| Custom YOLOv8n symbol detector | `SYMBOL_MODEL_AUTO_DOWNLOAD=false`, backend `heuristic` |
| VLM / LLM review models | `ENABLE_LLM_REVIEW_FALLBACK=false` |
| Separate geometry neural nets | Geometry stays OpenCV-only |

## Env (authoritative list also in `.env.example`)

- `MODEL_AUTO_DOWNLOAD=true`
- `MODEL_STARTUP_STRICT=true`
- `MODEL_CACHE_DIR=/models_cache`
- `OCR_BACKEND=paddleocr`
- `LAYOUT_BACKEND=yolov8n`
- `TABLE_BACKEND=paddle_table`
- `SHEET_CLASSIFIER_BACKEND=rules`
- `SYMBOL_DETECTION_BACKEND=heuristic`
- `REVIEW_BACKEND=rules`

## Health

- Per service: `GET /health` (503 if mandatory models missing / not loaded).
- Aggregated: `GET /api/v1/health/models` (Go API).
- MCP tool `health_check` includes `ml_service_health`.

## Scripts

- `scripts/bootstrap-models.sh` → runs `bootstrap_models.py`
- `scripts/check-models.sh` → verifies `bootstrap_status.json`

## Compatibility replacements

If a Paddle/Ultralytics minor version requires a compatible weight variant, document it here; backends must remain **PaddleOCR-class OCR**, **YOLOv8n-class layout**, **Paddle PP-Structure-class table**.

| Module | Default backend | Auto-installed on first start | Required |
|--------|-----------------|------------------------------|----------|
| OCR | PaddleOCR PP-OCRv4 det/rec/cls | yes | yes |
| Layout | YOLOv8n | yes | yes |
| Table structure | Paddle PP-Structure / SLANet-class | yes | yes |
| Sheet classifier | rule-based | no neural weights | module required |
| Symbol detector | heuristic | no | module required |
| Geometry extraction | OpenCV | no neural weights | yes |
| Dimension linking | rule-based | no neural weights | yes |
| Low-confidence review | rule-based | no neural weights | yes |
