# Pipeline

Statuses map to steps: unpacking → preprocessing → layout → geometry → ocr → assembling → exporting → packaging.

GPU-heavy calls are wrapped with a Redis distributed lock (`GPU_SEMAPHORE_KEY`) so only one inference stage runs at a time on a single gaming GPU by default.

`MOCK_PIPELINE=true` skips Python calls and generates a deterministic intermediate JSON for CI.
