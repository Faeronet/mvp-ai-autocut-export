"""Fail fast when ML inference must use GPU but CUDA is unavailable."""
from __future__ import annotations

import os
import sys


def _env_truthy(key: str) -> bool:
    return os.getenv(key, "").strip().lower() in ("1", "true", "yes")


def require_torch_cuda_if_layout_gpu(layout_use_gpu: bool) -> None:
    """Exit process if ML_REQUIRE_GPU is set but PyTorch cannot use CUDA."""
    if not _env_truthy("ML_REQUIRE_GPU"):
        return
    if not layout_use_gpu:
        return
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        print("FATAL: cannot import torch:", exc, file=sys.stderr)
        sys.exit(1)
    if not torch.cuda.is_available():
        print(
            "FATAL: ML_REQUIRE_GPU=true but torch.cuda.is_available() is false "
            "(install CUDA-enabled PyTorch image / drivers / NVIDIA runtime)",
            file=sys.stderr,
        )
        sys.exit(1)
    if torch.cuda.device_count() < 1:
        print("FATAL: ML_REQUIRE_GPU=true but torch.cuda.device_count() < 1", file=sys.stderr)
        sys.exit(1)
