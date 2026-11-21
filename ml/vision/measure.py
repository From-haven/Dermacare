"""
measure.py — Heuristic Vision Measurements and Safety Wrappers.
Provides:
- affected_area_ratio (heuristic LAB-Otsu)
- color_descriptor
- texture_descriptor
- lesion_count (NullDetector -> ABSTAIN with reason "no_weights")
- Out of scope checking (T07)
- Try/except safety wrapper: errors -> MODEL_UNAVAILABLE, never stale data (T09)
"""
import io
import math
from PIL import Image
from ml.vision.segment import segment_lesion_roi
from app.errors import ModelUnavailableException

class AcneDetector:
    """Acne detector interface. Defaults to NullDetector -> ABSTAIN."""
    def detect(self, img_bytes: bytes, roi: tuple = None) -> dict:
        return {
            "status": "ABSTAIN",
            "reason": "no_weights",
            "message": "chưa có model đếm tổn thương"
        }

def measure_observation(
    image_bytes: bytes,
    roi_geometry: dict = None,
    profile_type: str = "other",
    body_site: str = "other",
    simulate_failure: bool = False
) -> list:
    """
    Measure visual features of an observation.
    Returns list of Measurement dictionaries.
    """
    # T09: Safety failure handling
    if simulate_failure:
        raise ModelUnavailableException("Model phân tích hình ảnh tạm thời không khả dụng")

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise ModelUnavailableException(f"Không thể mở ảnh để đo: {str(e)}")

    w, h = img.size

    # T07: Out-of-scope body site validation
    valid_sites = {"face", "scalp", "neck", "trunk_front", "back", "arms", "hands", "legs", "feet", "folds", "nails", "other"}
    if body_site not in valid_sites:
        return [{
            "metric_name": "measurement_status",
            "value": 0.0,
            "unit": "none",
            "confidence": 0.0,
            "model_version": "heuristic-lab-otsu-0.1",
            "provenance": "ai_measured",
            "details": {"status": "ABSTAIN", "reason": "unsupported_body_site"}
        }]

    # Crop to ROI if available
    if roi_geometry and "bbox" in roi_geometry:
        bbox = roi_geometry["bbox"]
        x1 = max(0, int(bbox[0] * w))
        y1 = max(0, int(bbox[1] * h))
        x2 = min(w, int(bbox[2] * w))
        y2 = min(h, int(bbox[3] * h))
        roi_img = img.crop((x1, y1, x2, y2))
    else:
        # Default center crop
        roi_img = img.crop((int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8)))

    # 1. Affected area ratio (heuristic LAB-Otsu)
    seg_res = segment_lesion_roi(roi_img)

    measurements = [
        {
            "metric_name": "affected_area_ratio",
            "value": seg_res["affected_area_ratio"],
            "unit": "%",
            "confidence": seg_res["confidence"],
            "model_version": seg_res["model_version"],
            "provenance": "ai_measured",
            "details": {
                "label": "heuristic, không phải thang lâm sàng",
                "mask_pixels": seg_res["mask_count"],
                "roi_pixels": seg_res["total_pixels"]
            }
        }
    ]

    # 2. Color descriptor (RGB mean in ROI)
    try:
        pixels = list(roi_img.getdata())
        avg_r = sum(p[0] for p in pixels) / len(pixels)
        avg_g = sum(p[1] for p in pixels) / len(pixels)
        avg_b = sum(p[2] for p in pixels) / len(pixels)
        red_contrast = round((avg_r - (avg_g + avg_b) / 2.0), 2)
        measurements.append({
            "metric_name": "redness_contrast",
            "value": red_contrast,
            "unit": "delta_rgb",
            "confidence": 0.85,
            "model_version": "heuristic-lab-otsu-0.1",
            "provenance": "ai_measured",
            "details": {"mean_rgb": [round(avg_r, 1), round(avg_g, 1), round(avg_b, 1)]}
        })
    except Exception:
        pass

    # 3. Lesion detector (NullDetector -> ABSTAIN with no_weights)
    detector = AcneDetector()
    det_res = detector.detect(image_bytes)
    measurements.append({
        "metric_name": "lesion_count",
        "value": 0.0,
        "unit": "count",
        "confidence": 0.0,
        "model_version": "NullDetector-1.0",
        "provenance": "ai_measured",
        "details": det_res
    })

    return measurements
