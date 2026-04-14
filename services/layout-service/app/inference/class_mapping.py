from __future__ import annotations


CAD_LABELS = {
    0: "drawing_area",
    1: "title_block",
    2: "specification_table",
    3: "notes_block",
    4: "dimension_cluster",
    5: "border_frame",
}


def map_yolo_class(class_id: int, class_name: str | None = None) -> str:
    if class_id in CAD_LABELS:
        return CAD_LABELS[class_id]
    if class_name:
        n = class_name.lower().strip()
        if n in CAD_LABELS.values():
            return n
    return "unknown_region"
