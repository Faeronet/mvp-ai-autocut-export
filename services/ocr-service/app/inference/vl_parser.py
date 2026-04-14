from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import cv2


class Qwen25VLParser:
    """
    Qwen2.5-VL-3B semantic document parser.
    It is intentionally used as a semantic/document layer (regions, orientation, review hints),
    not as direct CAD geometry generator.
    """

    def __init__(
        self,
        enabled: bool,
        backend: str,
        device: str,
        use_fp16: bool,
        max_batch: int,
        model_id: str,
        max_new_tokens: int,
        quantization: str,
        use_flash_attention: bool,
    ) -> None:
        self.enabled = enabled
        self.backend = backend
        self.device = device
        self.use_fp16 = use_fp16
        self.max_batch = max(1, int(max_batch))
        self.model_id = model_id
        self.max_new_tokens = max(64, int(max_new_tokens))
        self.quantization = str(quantization).lower()
        self.use_flash_attention = use_flash_attention
        self._engine: Any = None
        self._processor: Any = None
        self._hf_model: Any = None
        self._hf_backend = False
        self._last_error: Optional[str] = None
        self._model_version = "qwen2.5-vl-3b"
        self._init_engine()

    def _init_engine(self) -> None:
        if not self.enabled:
            self._last_error = "vlm_disabled"
            return
        if self.backend not in ("qwen2_5_vl_3b", "hf_transformers"):
            self._last_error = f"unsupported_vlm_backend:{self.backend}"
            return
        self._init_hf_engine()

    def _init_hf_engine(self) -> None:
        try:
            import torch
            from transformers import AutoModel, AutoModelForImageTextToText, AutoProcessor

            dtype = torch.float16 if self.use_fp16 else torch.float32
            self._processor = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)
            quant_cfg = None
            if self.device.startswith("cuda") and self.quantization in ("4bit", "8bit"):
                try:
                    from transformers import BitsAndBytesConfig

                    quant_cfg = BitsAndBytesConfig(
                        load_in_4bit=self.quantization == "4bit",
                        load_in_8bit=self.quantization == "8bit",
                    )
                except Exception:
                    quant_cfg = None
            try:
                self._hf_model = AutoModelForImageTextToText.from_pretrained(
                    self.model_id,
                    trust_remote_code=True,
                    torch_dtype=dtype,
                    quantization_config=quant_cfg,
                    attn_implementation="eager" if not self.use_flash_attention else "flash_attention_2",
                )
            except Exception:
                self._hf_model = AutoModel.from_pretrained(
                    self.model_id,
                    trust_remote_code=True,
                    torch_dtype=dtype,
                    quantization_config=quant_cfg,
                )
            target_device = "cuda" if self.device.startswith("cuda") else "cpu"
            # Quantized model is device-mapped by transformers/bitsandbytes.
            if quant_cfg is None:
                self._hf_model = self._hf_model.to(target_device)
            self._hf_model = self._hf_model.eval()
            self._hf_backend = True
            self._model_version = f"hf:{self.model_id}"
            self._last_error = None
        except Exception as exc:  # noqa: BLE001
            self._last_error = f"hf_load_failed:{exc}"
            self._hf_backend = False
            self._processor = None
            self._hf_model = None

    @property
    def is_ready(self) -> bool:
        return self._engine is not None or self._hf_backend

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def model_version(self) -> str:
        return self._model_version

    def understand_page(self, image_path: str, profile: str) -> Dict[str, Any]:
        img = cv2.imread(image_path)
        if img is None:
            return {
                "sheet_type": "unknown",
                "regions": [],
                "orientation_hints": {},
                "review_hints": [],
                "warnings": ["cannot_read_image"],
                "model_version": self.model_version,
                "confidence": 0.0,
            }
        h, w = img.shape[:2]
        if not self.is_ready:
            return {
                "sheet_type": "mixed",
                "regions": [],
                "orientation_hints": {},
                "review_hints": [
                    {
                        "kind": "vlm_unavailable",
                        "reason": f"qwen2_5_vl_unavailable:{self._last_error or 'unknown'}",
                        "bbox_xyxy": [0.0, 0.0, float(w), float(h)],
                        "confidence": 0.0,
                    }
                ],
                "warnings": [f"qwen2_5_vl_unavailable:{self._last_error or 'unknown'}"],
                "model_version": self.model_version,
                "confidence": 0.0,
            }

        try:
            if self._hf_backend:
                raw = self._infer_with_hf(image_path)
            else:
                raw = self._engine.predict(image_path)  # type: ignore[operator]
        except Exception as exc:  # noqa: BLE001
            return {
                "sheet_type": "mixed",
                "regions": [],
                "orientation_hints": {},
                "review_hints": [
                    {
                        "kind": "vlm_infer_failed",
                        "reason": str(exc),
                        "bbox_xyxy": [0.0, 0.0, float(w), float(h)],
                        "confidence": 0.0,
                    }
                ],
                "warnings": [f"qwen2_5_vl_infer_failed:{exc}"],
                "model_version": self.model_version,
                "confidence": 0.0,
            }
        return _normalize_vlm_payload(raw, w, h, self.model_version)

    def _infer_with_hf(self, image_path: str) -> Dict[str, Any]:
        from PIL import Image
        import torch

        if self._processor is None or self._hf_model is None:
            raise RuntimeError("hf backend not initialized")
        image = Image.open(image_path).convert("RGB")
        prompt = (
            "Parse this engineering drawing page. Return strict JSON with keys: "
            "sheet_type, regions, orientation_hints, review_hints, warnings, confidence. "
            "regions items: {label,bbox_xyxy,confidence}. review_hints items: {kind,reason,bbox_xyxy,confidence}."
        )
        messages = [{"role": "user", "content": [{"type": "image", "image": image}, {"type": "text", "text": prompt}]}]
        inputs = self._processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )
        device = "cuda" if self.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
        if hasattr(inputs, "items"):
            inputs = {k: v.to(device) for k, v in inputs.items()}
        elif hasattr(inputs, "to"):
            inputs = inputs.to(device)
        else:
            raise RuntimeError("unexpected_processor_output")
        with torch.no_grad():
            if hasattr(inputs, "items"):
                outputs = self._hf_model.generate(**inputs, max_new_tokens=self.max_new_tokens)
                input_ids = inputs.get("input_ids")
            else:
                outputs = self._hf_model.generate(inputs, max_new_tokens=self.max_new_tokens)
                input_ids = None
        if hasattr(self._processor, "decode"):
            if input_ids is not None:
                text = self._processor.decode(outputs[0][input_ids.shape[-1] :], skip_special_tokens=True)
            else:
                text = self._processor.decode(outputs[0], skip_special_tokens=True)
        else:
            text = str(outputs)
        text = text.strip()
        # Strictly parse JSON, avoid using unconstrained model output as truth.
        try:
            return json.loads(text)
        except Exception:
            return {
                "sheet_type": "mixed",
                "regions": [],
                "orientation_hints": {},
                "review_hints": [
                    {
                        "kind": "vlm_non_json_output",
                        "reason": text[:400],
                        "bbox_xyxy": [0, 0, 0, 0],
                        "confidence": 0.0,
                    }
                ],
                "warnings": ["vlm_output_not_json"],
                "confidence": 0.0,
            }


def _normalize_vlm_payload(raw: Any, width: int, height: int, model_version: str) -> Dict[str, Any]:
    # Keep parser deterministic and strict: we only accept explicit, parseable fields.
    payload: Dict[str, Any] = raw if isinstance(raw, dict) else {}
    regions_in = payload.get("regions", [])
    regions: List[Dict[str, Any]] = []
    for r in regions_in:
        if not isinstance(r, dict):
            continue
        label = str(r.get("label", "unknown_region"))
        bbox = r.get("bbox_xyxy", [0, 0, width, height])
        if not isinstance(bbox, list) or len(bbox) < 4:
            bbox = [0, 0, width, height]
        regions.append(
            {
                "label": label,
                "bbox_xyxy": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                "confidence": float(r.get("confidence", 0.0)),
                "source": "vlm",
            }
        )
    hints_in = payload.get("review_hints", [])
    review_hints: List[Dict[str, Any]] = []
    for h in hints_in:
        if not isinstance(h, dict):
            continue
        bbox = h.get("bbox_xyxy", [0, 0, width, height])
        if not isinstance(bbox, list) or len(bbox) < 4:
            bbox = [0, 0, width, height]
        review_hints.append(
            {
                "kind": str(h.get("kind", "semantic_warning")),
                "reason": str(h.get("reason", "unspecified")),
                "bbox_xyxy": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                "confidence": float(h.get("confidence", 0.0)),
            }
        )
    return {
        "sheet_type": str(payload.get("sheet_type", "mixed")),
        "regions": regions,
        "orientation_hints": payload.get("orientation_hints", {}) if isinstance(payload.get("orientation_hints", {}), dict) else {},
        "review_hints": review_hints,
        "warnings": [str(w) for w in payload.get("warnings", [])] if isinstance(payload.get("warnings", []), list) else [],
        "model_version": model_version,
        "confidence": float(payload.get("confidence", 0.0)),
    }


# Backward compatibility alias for existing imports.
PaddleOCRVLParser = Qwen25VLParser
