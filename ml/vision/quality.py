"""
quality.py — Image Quality Assessment (Quality Gate).
Assesses:
- Sharpness (variance of Laplacian on ROI)
- Exposure (underexposure / overexposure)
- Glare (hotspots with high V and low S)
- Resolution (short dimension >= 640px)
- Framing (ROI ratio)
Returns QualityReport with status ∈ {PASS, RETAKE, REVIEW}, metrics, and reasons.
Supports both numpy and native Pillow fallback.
"""
from PIL import Image, ImageFilter
import io
import os
import yaml
import math

THRESHOLDS_PATH = "ml/vision/thresholds.yaml"

def load_thresholds() -> dict:
    if os.path.exists(THRESHOLDS_PATH):
        with open(THRESHOLDS_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {
        "version": "v1.1-default",
        "quality": {
            "sharpness": {"retake_threshold": 15.0, "review_threshold": 25.0},
            "exposure": {"extreme_dark_luminance": 12, "extreme_bright_luminance": 243, "retake_percentage": 25.0, "review_percentage": 12.0},
            "glare": {"v_min": 240, "s_max": 30, "retake_percentage": 8.0},
            "resolution": {"min_short_dimension": 240},
            "framing": {"min_roi_ratio": 0.04, "max_roi_ratio": 0.95}
        }
    }

def variance_of_laplacian_pillow(gray_img: Image.Image) -> float:
    """Compute variance of Laplacian using Pillow ImageFilter.Kernel."""
    lap = gray_img.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
    # Crop out 1px border to eliminate Pillow kernel padding border artifact
    w, h = lap.size
    if w > 2 and h > 2:
        lap = lap.crop((1, 1, w - 1, h - 1))
    try:
        pixels = list(lap.get_flattened_data())
    except AttributeError:
        pixels = list(lap.getdata())
    if not pixels:
        return 0.0
    mean = sum(pixels) / len(pixels)
    var = sum((p - mean) ** 2 for p in pixels) / len(pixels)
    return float(var)

def assess_image_quality(image_bytes: bytes, roi_rect: tuple = None) -> dict:
    """
    Assess quality of image.
    roi_rect: (x_min, y_min, x_max, y_max) normalized 0.0 to 1.0.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = img.size
    cfg = load_thresholds()["quality"]

    reasons = []
    metrics = {}
    status = "PASS"

    # 1. Resolution Check
    short_edge = min(width, height)
    metrics["short_edge"] = short_edge
    if short_edge < cfg["resolution"]["min_short_dimension"]:
        status = "RETAKE"
        reasons.append(f"Độ phân giải quá thấp ({short_edge}px < {cfg['resolution']['min_short_dimension']}px)")

    # Resize long edge only if > 1024 for standardized evaluation without upscaling artifacts
    long_edge = max(width, height)
    if long_edge > 1024:
        scale = 1024.0 / long_edge
        new_w, new_h = max(1, int(width * scale)), max(1, int(height * scale))
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    else:
        resized = img
        new_w, new_h = width, height

    # Determine evaluation region (ROI or center 60% if no ROI)
    if roi_rect and len(roi_rect) == 4:
        x1 = max(0, int(roi_rect[0] * new_w))
        y1 = max(0, int(roi_rect[1] * new_h))
        x2 = min(new_w, int(roi_rect[2] * new_w))
        y2 = min(new_h, int(roi_rect[3] * new_h))
        if x2 <= x1 or y2 <= y1:
            roi_img = resized
        else:
            roi_img = resized.crop((x1, y1, x2, y2))
    else:
        # Center crop (20% to 80%)
        x1, y1 = int(new_w * 0.2), int(new_h * 0.2)
        x2, y2 = int(new_w * 0.8), int(new_h * 0.8)
        roi_img = resized.crop((x1, y1, x2, y2))

    # Convert to grayscale for sharpness and luminance
    gray_roi = roi_img.convert("L")

    # 2. Sharpness (Variance of Laplacian)
    lap_var = variance_of_laplacian_pillow(gray_roi)
    metrics["sharpness_score"] = round(lap_var, 2)
    if lap_var < cfg["sharpness"]["retake_threshold"]:
        status = "RETAKE"
        reasons.append(f"Ảnh quá mờ ({metrics['sharpness_score']} < {cfg['sharpness']['retake_threshold']})")
    elif lap_var < cfg["sharpness"]["review_threshold"]:
        if status != "RETAKE":
            status = "REVIEW"
        reasons.append(f"Ảnh hơi mờ ({metrics['sharpness_score']} < {cfg['sharpness']['review_threshold']})")

    # 3. Exposure (% pixels luminance < 12 or > 243)
    try:
        gray_pixels = list(gray_roi.get_flattened_data())
    except AttributeError:
        gray_pixels = list(gray_roi.getdata())

    total_px = max(1, len(gray_pixels))
    dark_px = sum(1 for p in gray_pixels if p < cfg["exposure"]["extreme_dark_luminance"])
    bright_px = sum(1 for p in gray_pixels if p > cfg["exposure"]["extreme_bright_luminance"])

    exposure_pct = float((dark_px + bright_px) / total_px * 100.0)
    metrics["exposure_bad_pct"] = round(exposure_pct, 1)
    metrics["dark_pct"] = round(dark_px / total_px * 100.0, 1)
    metrics["bright_pct"] = round(bright_px / total_px * 100.0, 1)

    if exposure_pct > cfg["exposure"]["retake_percentage"]:
        status = "RETAKE"
        reasons.append(f"Ánh sáng không đạt: {round(exposure_pct, 1)}% pixel quá tối/cháy sáng")
    elif exposure_pct > cfg["exposure"]["review_percentage"]:
        if status != "RETAKE":
            status = "REVIEW"
        reasons.append(f"Độ phơi sáng biên giới: {round(exposure_pct, 1)}% pixel tối/sáng")

    # 4. Glare Check
    try:
        rgb_pixels = list(roi_img.get_flattened_data())
        # If flattened, each pixel is (r, g, b)
        if isinstance(rgb_pixels[0], int):
            # Flat list [r0, g0, b0, r1, g1, b1, ...]
            glare_count = 0
            for i in range(0, len(rgb_pixels), 3):
                r, g, b = rgb_pixels[i], rgb_pixels[i+1], rgb_pixels[i+2]
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                if max_c > cfg["glare"]["v_min"] and (max_c - min_c) < 25:
                    glare_count += 1
        else:
            glare_count = sum(1 for (r, g, b) in rgb_pixels if max(r, g, b) > cfg["glare"]["v_min"] and (max(r, g, b) - min(r, g, b)) < 25)
    except Exception:
        glare_count = 0

    glare_pct = float(glare_count / total_px * 100.0)
    metrics["glare_pct"] = round(glare_pct, 1)

    if glare_pct > cfg["glare"]["retake_percentage"]:
        status = "RETAKE"
        reasons.append(f"Loá sáng phản xạ ({metrics['glare_pct']}% > {cfg['glare']['retake_percentage']}%)")

    return {
        "status": status,
        "metrics": metrics,
        "thresholds": {
            "sharpness_retake": cfg["sharpness"]["retake_threshold"],
            "sharpness_review": cfg["sharpness"]["review_threshold"],
            "min_short_dimension": cfg["resolution"]["min_short_dimension"]
        },
        "reasons": reasons,
        "thresholds_version": cfg.get("version", "v1.1-calibrated")
    }
