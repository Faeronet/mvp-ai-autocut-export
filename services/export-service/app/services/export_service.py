from __future__ import annotations

from typing import Any, Dict

from app.exporters.clean_preview import render_clean_preview
from app.exporters.diagnostic_preview import render_diagnostic_preview
from app.exporters.dxf_exporter import export_dxf


class ExportService:
    def render(self, intermediate: Dict[str, Any], output_dxf: str, output_png: str, profile: str) -> Dict[str, str]:
        diag_path = output_png.replace(".png", "_diagnostic.png")
        export_dxf(intermediate, output_dxf)
        render_clean_preview(intermediate, output_png)
        render_diagnostic_preview(intermediate, diag_path)
        return {"dxf_path": output_dxf, "png_path": output_png, "diagnostic_png_path": diag_path}
