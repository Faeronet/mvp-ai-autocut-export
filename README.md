# DrawDigit MVP

Production-like MVP for digitizing scanned mechanical drawings into AutoCAD-friendly **DXF**, with **PNG previews**, structured **JSON**, a **React** control panel, **async** jobs on **Redis + PostgreSQL**, and an **MCP** (Model Context Protocol) HTTP server.

## Architecture (short)

- **Go**: `api` (REST + SSE + metrics), `worker` (pipeline + GPU lock), `mcp` (JSON-RPC HTTP + stdio).
- **Python**: `layout-service`, `ocr-service`, `vector-service`, `export-service` (FastAPI).
- **Data**: Postgres metadata, Redis queue + distributed GPU lock, `./data` bind mount for archives/artifacts.

See `docs/architecture.md` and `docs/code-structure.md`.
Remote training guide: `docs/training-layout-remote.md`.

## Assumptions / MVP limits

- **DXF** is the primary CAD export; **DWG** is not generated (extensible via exporter interface).
- **Mandatory model pack** (auto-downloaded on first compose via `bootstrap-models`): **PaddleOCR PP-OCRv4** (det/rec/cls), **Paddle PP-Structure** table backend, **YOLOv8n** layout baseline. Geometry remains **OpenCV** (no NN). Details: `docs/model-management.md`.
- `MOCK_PIPELINE=true` validates orchestration without calling Python ML services.

## Quick start (Docker Compose, Ubuntu 22.04)

1. Install [Docker](https://docs.docker.com/engine/install/ubuntu/) and the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
2. `cp .env.example .env` and adjust GPU-related variables.
3. From repo root:

```bash
make docker-up
```

The **`bootstrap-models`** service runs once before `layout-service` / `ocr-service` and fills the `models_cache` volume. Re-runs reuse cached weights.

- UI: `http://localhost` or `http://<server-ip>` (nginx → static web + `/api` proxy to `api:8080`; ports bind to `0.0.0.0` for LAN/public access)
- API: `http://localhost:8080` (also `http://<server-ip>:8080` if exposed)
- MCP: `http://localhost:8090/mcp`

External access: open firewall for ports **80** (UI), optionally **8080**/**8090**; defaults `CORS_ALLOWED_ORIGINS=*` and `MCP_ALLOWED_HOSTS` include `*` for development-style exposure — tighten for production (see `docs/deployment.md`).

### Local development (no Docker)

1. Start Postgres + Redis locally.
2. Export env from `.env.example`.
3. `go run ./cmd/api` and `go run ./cmd/worker` in separate shells.
4. Start Python services via `uvicorn` on ports 8001–8004.
5. `cd apps/web && npm install && npm run dev`.

## Makefile targets

- `make test` — Go unit tests
- `make build` — compile Go binaries into `./bin`
- `make web` — production build of the SPA
- `make docker-up` / `make docker-down` — compose lifecycle

## Environment

See `.env.example` for the authoritative list (`POSTGRES_DSN`, `REDIS_ADDR`, `DATA_DIR`, GPU tuning, `MOCK_PIPELINE`, MCP/CORS settings).

## REST API (outline)

- `POST /api/v1/jobs/upload` — multipart `file`, optional `profile`
- `GET /api/v1/jobs/{id}`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{id}/report`
- `GET /api/v1/jobs/{id}/download`
- `GET /api/v1/jobs/{id}/events` — SSE polling stream
- `POST /api/v1/jobs/{id}/cancel`
- `POST /api/v1/jobs/{id}/retry`
- `GET /api/v1/health`
- `GET /api/v1/health/models` — aggregated ML service model status
- `GET /api/v1/config/profiles`
- `GET /metrics`

OpenAPI sketch: `docs/openapi.yaml`.

## MCP surface

**Tools**: `submit_archive`, `get_job_status`, `list_job_outputs`, `download_result_info`, `get_job_report`, `cancel_job`, `retry_job`, `health_check`.

**Resources**: `job://{id}/manifest|report|...`, `system://profiles`, `system://health`.

**Prompts**: registered names mirror `prompts/mcp/*.md`.

Details: `docs/mcp.md`.

## Tests

```bash
go test ./...
pytest -q services/ocr-service/tests services/layout-service/tests services/vector-service/tests
```

## Phase 1 baseline notes

- Layout now uses deterministic zoning as primary behavior; percent-based boxes are only last-resort fallback with explicit warning.
- OCR uses ROI routing with engineering-aware normalization and RU-oriented language policy (`OCR_LANG=ru` by default).
- Table structure step is integrated into the main pipeline and included in `intermediate.json`.
- Preprocessing writes debug artifacts under per-page work dir (`debug/preprocess/*`) and produces OCR + geometry branches.
- Export writes two previews: clean (`preview.png`) and diagnostic (`preview_diagnostic.png`).

## Troubleshooting

See `docs/troubleshooting.md` (VRAM, OCR, locks).

## License

MIT (adjust as needed).
