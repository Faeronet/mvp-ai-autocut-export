from pathlib import Path

import cv2
import numpy as np

from app.preprocessing.document_normalizer import normalize_document


def test_document_normalizer_outputs_branches(tmp_path: Path):
    src = tmp_path / "src.png"
    img = np.full((400, 500, 3), 255, dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (480, 380), (0, 0, 0), 2)
    cv2.imwrite(str(src), img)

    out = normalize_document(str(src), str(tmp_path / "work"), max_side=1024)
    assert Path(out.preprocessed_path).exists()
    assert Path(out.binary_path).exists()
    assert Path(out.soft_path).exists()
    assert "raw" in out.debug_artifacts
