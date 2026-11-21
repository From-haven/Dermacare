"""
roi.py — Region of Interest (ROI) Localization.
Handles user-drawn ROI, face landmarks, and center fallbacks.
Coordinates are normalized in range [0.0, 1.0].
"""
from typing import Tuple, Dict, Any

def get_default_roi(body_site: str) -> Dict[str, Any]:
    """Default normalized rectangular ROI (center 60%)."""
    return {
        "method": "auto",
        "geometry": {
            "type": "rect",
            "bbox": [0.2, 0.2, 0.8, 0.8]  # x_min, y_min, x_max, y_max
        }
    }

def validate_roi(geometry: dict) -> bool:
    """Validate normalized coordinates."""
    if not isinstance(geometry, dict):
        return False
    bbox = geometry.get("bbox")
    if not bbox or len(bbox) != 4:
        return False
    x1, y1, x2, y2 = bbox
    return 0.0 <= x1 < x2 <= 1.0 and 0.0 <= y1 < y2 <= 1.0
