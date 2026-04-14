# Processing profiles

- `balanced`: default resize/denoise, GPU flags on.
- `quality`: larger inputs, more debug outputs in preprocess.
- `low_vram`: aggressive `MAX_IMAGE_SIDE`, sequential behavior implied by worker lock and reduced concurrency.

Compose mirrors GPU tiers via `PROFILE_GPU_*` env presets (8/12/16 GB) — adjust `MAX_IMAGE_SIDE`, `TILE_SIZE`, and `MAX_PARALLEL_JOBS`.
