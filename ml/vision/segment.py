"""
segment.py — Heuristic Lesion Segmentation (heuristic-lab-otsu-0.1).
Converts ROI to LAB color space, extracts a* channel (redness),
normalizes using median and MAD (Median Absolute Deviation),
and applies Otsu thresholding with morphological open/close to segment lesion areas.
Optimized with thumbnail pre-scaling (<= 256px) for < 50ms runtime on multi-megapixel images.
"""
from PIL import Image, ImageFilter
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
    Segment lesion within ROI image using LAB a* channel + Otsu + Morphological filtering.
    Optimized: downscales ROI to max 256px before pixel loops.
    Returns:
    - affected_area_ratio: % area of lesion in ROI
    - component_count: number of distinct connected lesion components
    - dispersion: spatial dispersion of components [0.0, 1.0]
    - texture: standard deviation of lightness inside lesion
    - light_contrast: delta L* between lesion and background
    - redness_contrast: delta a* between lesion and background
    - color_descriptor: dict of lab means and stds
    - texture_descriptor: dict of variance
    - confidence: float [0, 1]
    - mask_count: number of lesion pixels
    """
    orig_w, orig_h = roi_img.size
    total_px_orig = orig_w * orig_h
    if total_px_orig == 0:
        return {
            "affected_area_ratio": 0.0,
            "component_count": 0,
            "dispersion": 0.0,
            "texture": 0.0,
            "light_contrast": 0.0,
            "redness_contrast": 0.0,
            "confidence": 0.0,
            "mask_count": 0,
            "total_pixels": 0,
            "model_version": "heuristic-lab-otsu-0.1"
        }

    # FIX-08: Resize to thumbnail (max 256px) for sub-50ms CPU execution
    max_dim = 256
    if max(orig_w, orig_h) > max_dim:
        scale = max_dim / max(orig_w, orig_h)
        thumb_w = max(1, int(orig_w * scale))
        thumb_h = max(1, int(orig_h * scale))
        thumb_img = roi_img.resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
    else:
        thumb_w, thumb_h = orig_w, orig_h
        thumb_img = roi_img

    total_px = thumb_w * thumb_h
    # Extract LAB values
    raw_rgb = thumb_img.convert("RGB").tobytes()
    l_values = []
    a_values = []
    b_values = []
    for i in range(0, len(raw_rgb), 3):
        L, a, b_val = rgb_to_lab(raw_rgb[i], raw_rgb[i+1], raw_rgb[i+2])
        l_values.append(L)
        a_values.append(a)
        b_values.append(b_val)

    # Median and MAD normalization on a*
    sorted_a = sorted(a_values)
    median_a = sorted_a[len(sorted_a) // 2]
    abs_diffs = sorted(abs(x - median_a) for x in a_values)
    mad_a = max(0.1, abs_diffs[len(abs_diffs) // 2])

    normalized_a = [(x - median_a) / mad_a for x in a_values]

    # Otsu thresholding on normalized redness
    thresh = otsu_threshold(normalized_a)
    effective_thresh = max(0.5, thresh)

    # Build raw binary mask (255 for lesion, 0 for background)
    raw_mask_bytes = bytearray(255 if na > effective_thresh else 0 for na in normalized_a)
    mask_img = Image.frombytes("L", (thumb_w, thumb_h), bytes(raw_mask_bytes))

    # FIX-04: Morphological open (erode then dilate) to eliminate isolated noise
    # and morphological close (dilate then erode) to close small holes
    mask_open = mask_img.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    mask_filtered = mask_open.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))

    filtered_bytes = list(mask_filtered.tobytes())

    # Connected component labeling (8-connectivity BFS) & filtering components < 0.05% of ROI
    visited = [False] * total_px
    min_comp_px = max(2, int(total_px * 0.0005))  # 0.05% of ROI
    components = []

    for idx in range(total_px):
        if filtered_bytes[idx] == 255 and not visited[idx]:
            # BFS for component
            comp_pixels = []
            queue = [idx]
            visited[idx] = True
            while queue:
                curr = queue.pop(0)
                comp_pixels.append(curr)
                cy = curr // thumb_w
                cx = curr % thumb_w
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < thumb_h and 0 <= nx < thumb_w:
                            nidx = ny * thumb_w + nx
                            if filtered_bytes[nidx] == 255 and not visited[nidx]:
                                visited[nidx] = True
                                queue.append(nidx)

            if len(comp_pixels) >= min_comp_px:
                components.append(comp_pixels)

    # Final lesion mask indices after component filtering
    final_lesion_indices = set()
    for comp in components:
        final_lesion_indices.update(comp)

    lesion_pixels_count = len(final_lesion_indices)
    ratio = (lesion_pixels_count / total_px) * 100.0

    # Calculate statistics inside vs outside lesion
    if lesion_pixels_count > 0:
        lesion_l = [l_values[i] for i in final_lesion_indices]
        lesion_a = [a_values[i] for i in final_lesion_indices]
        lesion_b = [b_values[i] for i in final_lesion_indices]

        bg_indices = [i for i in range(total_px) if i not in final_lesion_indices]
        if bg_indices:
            bg_l = [l_values[i] for i in bg_indices]
            bg_a = [a_values[i] for i in bg_indices]
            mean_bg_l = sum(bg_l) / len(bg_l)
            mean_bg_a = sum(bg_a) / len(bg_a)
        else:
            mean_bg_l = 50.0
            mean_bg_a = 0.0

        mean_lesion_l = sum(lesion_l) / len(lesion_l)
        mean_lesion_a = sum(lesion_a) / len(lesion_a)
        mean_lesion_b = sum(lesion_b) / len(lesion_b)

        light_contrast = round(abs(mean_lesion_l - mean_bg_l), 2)
        redness_contrast = round(mean_lesion_a - mean_bg_a, 2)

        # Texture inside lesion (std of L)
        variance_l = sum((x - mean_lesion_l) ** 2 for x in lesion_l) / len(lesion_l)
        texture_val = round(math.sqrt(variance_l) / 100.0, 3)

        # Dispersion: standard deviation of component centroids normalized by ROI diagonal
        diag = math.sqrt(thumb_w * thumb_w + thumb_h * thumb_h)
        if len(components) > 1:
            centroids = []
            for c in components:
                cx = sum(p % thumb_w for p in c) / len(c)
                cy = sum(p // thumb_w for p in c) / len(c)
                centroids.append((cx, cy))
            avg_cx = sum(c[0] for c in centroids) / len(centroids)
            avg_cy = sum(c[1] for c in centroids) / len(centroids)
            dist_sq = sum((c[0] - avg_cx) ** 2 + (c[1] - avg_cy) ** 2 for c in centroids) / len(centroids)
            dispersion_val = round(min(1.0, math.sqrt(dist_sq) / max(1.0, diag * 0.5)), 3)
        else:
            dispersion_val = 0.0
    else:
        light_contrast = 0.0
        redness_contrast = 0.0
        texture_val = 0.0
        dispersion_val = 0.0
        mean_lesion_l, mean_lesion_a, mean_lesion_b = 50.0, 0.0, 0.0

    contrast_span = abs(max(normalized_a) - min(normalized_a))
    confidence = min(0.95, max(0.40, contrast_span / 5.0))

    return {
        "affected_area_ratio": round(ratio, 2),
        "component_count": len(components),
        "dispersion": dispersion_val,
        "texture": texture_val,
        "light_contrast": light_contrast,
        "redness_contrast": redness_contrast,
        "color_descriptor": {
            "mean_lab": [round(mean_lesion_l, 1), round(mean_lesion_a, 1), round(mean_lesion_b, 1)]
        },
        "texture_descriptor": {"std_lightness": texture_val},
        "confidence": round(confidence, 2),
        "mask_count": lesion_pixels_count,
        "total_pixels": total_px,
        "model_version": "heuristic-lab-otsu-0.1"
    }
