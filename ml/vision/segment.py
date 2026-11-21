"""
segment.py — Heuristic Lesion Segmentation (heuristic-lab-otsu-0.1).
Converts ROI to LAB color space, extracts a* channel (redness),
normalizes using median and MAD (Median Absolute Deviation),
and applies Otsu thresholding to segment lesion areas.
"""
from PIL import Image
import math
import io

def rgb_to_lab(r: float, g: float, b: float) -> tuple:
    """Convert sRGB (0-255) to CIE LAB."""
    # Convert sRGB to linear RGB
    r_l = r / 255.0
    g_l = g / 255.0
    b_l = b / 255.0

    r_l = ((r_l + 0.055) / 1.055) ** 2.4 if r_l > 0.04045 else r_l / 12.92
    g_l = ((g_l + 0.055) / 1.055) ** 2.4 if g_l > 0.04045 else g_l / 12.92
    b_l = ((b_l + 0.055) / 1.055) ** 2.4 if b_l > 0.04045 else b_l / 12.92

    # Linear RGB to XYZ (D65)
    x = r_l * 0.4124564 + g_l * 0.3575761 + b_l * 0.1804375
    y = r_l * 0.2126729 + g_l * 0.7151522 + b_l * 0.0721750
    z = r_l * 0.0193339 + g_l * 0.1191920 + b_l * 0.9503041

    # D65 reference white
    x_n, y_n, z_n = 0.95047, 1.00000, 1.08883
    x_r, y_r, z_r = x / x_n, y / y_n, z / z_n

    fx = x_r ** (1/3) if x_r > 0.008856 else (7.787 * x_r) + (16 / 116)
    fy = y_r ** (1/3) if y_r > 0.008856 else (7.787 * y_r) + (16 / 116)
    fz = z_r ** (1/3) if z_r > 0.008856 else (7.787 * z_r) + (16 / 116)

    L = max(0.0, (116.0 * fy) - 16.0)
    a = 500.0 * (fx - fy)
    b_val = 200.0 * (fy - fz)
    return L, a, b_val

def otsu_threshold(values: list) -> float:
    """Compute Otsu's optimal threshold for a 1D list of float values."""
    if not values:
        return 0.0
    # Discretize into 256 bins
    min_v = min(values)
    max_v = max(values)
    if math.isclose(min_v, max_v):
        return min_v

    bins = [0] * 256
    scale = 255.0 / (max_v - min_v)
    for v in values:
        idx = min(255, max(0, int((v - min_v) * scale)))
        bins[idx] += 1

    total = len(values)
    sum_total = sum(i * bins[i] for i in range(256))

    sum_b = 0
    w_b = 0
    max_variance = 0.0
    best_thresh_idx = 128

    for t in range(256):
        w_b += bins[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * bins[t]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        between_var = w_b * w_f * ((m_b - m_f) ** 2)
        if between_var > max_variance:
            max_variance = between_var
            best_thresh_idx = t

    return min_v + (best_thresh_idx / scale)

def segment_lesion_roi(roi_img: Image.Image) -> dict:
    """
    Segment lesion within ROI image using LAB a* channel + Otsu.
    Returns:
    - affected_area_ratio: % area of lesion in ROI
    - confidence: float [0, 1]
    - mask_count: number of lesion pixels
    """
    w, h = roi_img.size
    total_px = w * h
    if total_px == 0:
        return {"affected_area_ratio": 0.0, "confidence": 0.0, "mask_count": 0}

    # Extract LAB a* values for all pixels
    a_values = []
    l_values = []
    pixels = list(roi_img.getdata())
    for p in pixels:
        L, a, _ = rgb_to_lab(p[0], p[1], p[2])
        a_values.append(a)
        l_values.append(L)

    # Median and MAD normalization on a*
    sorted_a = sorted(a_values)
    median_a = sorted_a[len(sorted_a) // 2]
    abs_diffs = sorted(abs(x - median_a) for x in a_values)
    mad_a = max(0.1, abs_diffs[len(abs_diffs) // 2])

    normalized_a = [(x - median_a) / mad_a for x in a_values]

    # Otsu thresholding on normalized redness
    thresh = otsu_threshold(normalized_a)
    # Lesions have elevated redness (a* > threshold and threshold > 0.5)
    effective_thresh = max(0.5, thresh)

    lesion_pixels = sum(1 for na in normalized_a if na > effective_thresh)
    ratio = (lesion_pixels / total_px) * 100.0

    # Confidence score based on contrast separation
    contrast = abs(max(normalized_a) - min(normalized_a))
    confidence = min(0.95, max(0.40, contrast / 5.0))

    return {
        "affected_area_ratio": round(ratio, 2),
        "confidence": round(confidence, 2),
        "mask_count": lesion_pixels,
        "total_pixels": total_px,
        "model_version": "heuristic-lab-otsu-0.1"
    }
