"""Runtime model registry for health reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ModelStatus:
    model_name: str
    installed: bool
    loaded: bool
    version: str
    backend: str
    device: str
    last_error: Optional[str] = None


@dataclass
class Registry:
    models: Dict[str, ModelStatus] = field(default_factory=dict)

    def set(self, m: ModelStatus) -> None:
        self.models[m.model_name] = m

    def to_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "model_name": m.model_name,
                "installed": m.installed,
                "loaded": m.loaded,
                "version": m.version,
                "backend": m.backend,
                "device": m.device,
                "last_error": m.last_error,
            }
            for m in self.models.values()
        ]

    def all_ready(self) -> bool:
        return all(m.loaded and m.installed for m in self.models.values() if m.model_name.startswith("required:"))


REGISTRY = Registry()
