# Troubleshooting

- **OOM / CUDA errors**: set `MOCK_PIPELINE=true` to validate orchestration, then lower `MAX_IMAGE_SIDE`, ensure `MAX_GPU_TASKS=1`, and verify only one worker replica runs GPU jobs.
- **OCR empty results**: confirm `tesseract-ocr` is installed in the OCR container and input ROIs are valid.
- **DXF empty**: check `intermediate.json` in the job workspace; export service logs will show Python tracebacks.
- **Redis lock stuck**: flush `GPU_SEMAPHORE_KEY` or restart Redis during development only.
