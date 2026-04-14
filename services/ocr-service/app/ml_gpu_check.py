"""Fail fast when ML inference must use GPU but CUDA is unavailable."""
from __future__ import annotations

import os
import sys


def _env_truthy(key: str) -> bool:
    return os.getenv(key, "").strip().lower() in ("1", "true", "yes")


def require_paddle_cuda_if_configured(ocr_use_gpu: bool, table_use_gpu: bool) -> None:
    """Exit process if ML_REQUIRE_GPU is set but Paddle cannot see a CUDA device."""
    if not _env_truthy("ML_REQUIRE_GPU"):
        return
    if not (ocr_use_gpu or table_use_gpu):
        return
    try:
        import paddle
    except Exception as exc:  # noqa: BLE001
        print("FATAL: cannot import paddle:", exc, file=sys.stderr)
        sys.exit(1)
    compiled = getattr(paddle, "is_compiled_with_cuda", lambda: False)()
    if not compiled:
        print("FATAL: ML_REQUIRE_GPU=true but Paddle is not built with CUDA", file=sys.stderr)
        sys.exit(1)
    n = paddle.device.cuda.device_count()
    if n < 1:
        print(
            "FATAL: ML_REQUIRE_GPU=true but no GPU visible to Paddle "
            "(check NVIDIA Container Toolkit, CUDA_VISIBLE_DEVICES, and drivers)",
            file=sys.stderr,
        )
        sys.exit(1)
