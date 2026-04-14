import cv2
import numpy as np

from app.postprocessing.geometry_extract import extract_geometry


def test_geometry_extract_no_global_circles_baseline():
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    out = extract_geometry(img)
    assert isinstance(out["lines"], list)
    assert out["circles"] == []
    assert isinstance(out["tables"], list)
    assert len(out["tables"]) == 1
    assert "bbox_xyxy" in out["tables"][0]


def test_geometry_extract_horizontal_line_in_drawing_area():
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    cv2.line(img, (120, 200), (500, 200), (255, 255, 255), 2)
    out = extract_geometry(img)
    assert isinstance(out["lines"], list)
    geom = [ln for ln in out["lines"] if ln.get("layer") == "GEOMETRY"]
    assert len(geom) >= 1
