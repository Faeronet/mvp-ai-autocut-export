from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IterationConfig:
    iteration_id: int
    profile: str
    api_base: str
    poll_seconds: float
    timeout_seconds: int
    test_metr_dir: Path
    experiments_dir: Path

    @property
    def iter_dir(self) -> Path:
        return self.experiments_dir / f"iter_{self.iteration_id:03d}"
