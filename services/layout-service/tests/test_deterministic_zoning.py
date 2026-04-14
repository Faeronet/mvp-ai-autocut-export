import numpy as np

from app.inference.deterministic_zoning import deterministic_zones


def test_deterministic_zones_produce_core_labels():
    img = np.full((800, 1200, 3), 255, dtype=np.uint8)
    zones, _ = deterministic_zones(img)
    labels = {z.label for z in zones}
    assert "drawing_area" in labels
    assert "title_block" in labels
    assert "specification_table" in labels
