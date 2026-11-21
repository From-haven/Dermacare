"""
measure.py — Heuristic Vision Measurements and Safety Wrappers.
Provides:
- affected_area_ratio (heuristic LAB-Otsu)
- redness_contrast (delta a*)
- component_count (number of connected lesion components)
- dispersion (spatial spread of components)
- texture (lightness variation inside lesion)
- light_contrast (delta L*)
- color_descriptor & texture_descriptor
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
    Returns list of Measurement dictionaries with provenance='ai_measured'.
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
        roi_img = img.crop((int(w * 0.15), int(h * 0.15), int(w * 0.85), int(h * 0.85)))

    # Segment lesion and compute all 6 visual metrics
    seg_res = segment_lesion_roi(roi_img)

    measurements = [
        # 1. Affected area ratio
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
        },
        # 2. Redness contrast
        {
            "metric_name": "redness_contrast",
            "value": seg_res["redness_contrast"],
            "unit": "delta_a",
            "confidence": seg_res["confidence"],
            "model_version": seg_res["model_version"],
            "provenance": "ai_measured",
            "details": {"color_descriptor": seg_res["color_descriptor"]}
        },
        # 3. Component count
        {
            "metric_name": "component_count",
            "value": float(seg_res["component_count"]),
            "unit": "count",
            "confidence": seg_res["confidence"],
            "model_version": seg_res["model_version"],
            "provenance": "ai_measured",
            "details": {"component_count": seg_res["component_count"]}
        },
        # 4. Dispersion
        {
            "metric_name": "dispersion",
            "value": seg_res["dispersion"],
            "unit": "normalized",
            "confidence": seg_res["confidence"],
            "model_version": seg_res["model_version"],
            "provenance": "ai_measured",
            "details": {"spatial_dispersion": seg_res["dispersion"]}
        },
        # 5. Texture
        {
            "metric_name": "texture",
            "value": seg_res["texture"],
            "unit": "normalized",
            "confidence": seg_res["confidence"],
            "model_version": seg_res["model_version"],
            "provenance": "ai_measured",
            "details": {"texture_descriptor": seg_res["texture_descriptor"]}
        },
        # 6. Light contrast
        {
            "metric_name": "light_contrast",
            "value": seg_res["light_contrast"],
            "unit": "delta_L",
            "confidence": seg_res["confidence"],
            "model_version": seg_res["model_version"],
            "provenance": "ai_measured",
            "details": {"delta_lightness": seg_res["light_contrast"]}
        },
        # 7. Lesion detector (NullDetector -> ABSTAIN with no_weights)
        {
            "metric_name": "lesion_count",
            "value": 0.0,
            "unit": "count",
            "confidence": 0.0,
            "model_version": "NullDetector-1.0",
            "provenance": "ai_measured",
            "details": AcneDetector().detect(image_bytes)
        }
    ]

    return measurements
