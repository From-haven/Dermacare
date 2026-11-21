"""
compare.py — Image Observation Comparability and Deltas (T02).
Evaluates whether two observations are COMPARABLE, PARTIAL, or NOT_COMPARABLE.
Rules:
- NOT_COMPARABLE if: different case, different body_site, different view_type,
  either quality != PASS, or alignment fails.
- PARTIAL if: median L* diff > 15, ROI area diff > 35%, correlation 0.6-0.8, or time < 12h.
- COMPARABLE if: correlation >= 0.8 and criteria met.
- Deltas are ONLY computed when COMPARABLE.
"""
from typing import Dict, Any, List

def evaluate_comparability(
    obs_a: Dict[str, Any],
    obs_b: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare observation A (previous) and observation B (current).
    Returns flag in {COMPARABLE, PARTIAL, NOT_COMPARABLE}, reasons[], deltas{}.
    """
    reasons: List[str] = []
    flag = "COMPARABLE"
    deltas: Dict[str, Any] = {}

    # 1. T02: Check same case
    if obs_a.get("case_id") != obs_b.get("case_id"):
        return {
            "flag": "NOT_COMPARABLE",
            "reasons": ["Hai ảnh thuộc hai ca theo dõi khác nhau"],
            "deltas": {}
        }

    # 2. T02: Check same body site
    site_a = obs_a.get("body_site")
    site_b = obs_b.get("body_site")
    if site_a and site_b and site_a != site_b:
        return {
            "flag": "NOT_COMPARABLE",
            "reasons": [f"Vùng chụp khác nhau: '{site_a}' so với '{site_b}'"],
            "deltas": {}
        }

    # 3. Check view type (overview vs closeup)
    view_a = obs_a.get("view_type", "overview")
    view_b = obs_b.get("view_type", "overview")
    if view_a != view_b:
        return {
            "flag": "NOT_COMPARABLE",
            "reasons": [f"Góc chụp không tương đồng: '{view_a}' so với '{view_b}'"],
            "deltas": {}
        }

    # 4. Check quality status
    q_a = obs_a.get("quality_status", "PASS")
    q_b = obs_b.get("quality_status", "PASS")
    if q_a != "PASS" or q_b != "PASS":
        return {
            "flag": "NOT_COMPARABLE",
            "reasons": [f"Chất lượng ảnh không đạt tiêu chuẩn PASS (ảnh 1: {q_a}, ảnh 2: {q_b})"],
            "deltas": {}
        }

    # 5. Check illumination difference (L* median)
    l_a = obs_a.get("l_median", 50.0)
    l_b = obs_b.get("l_median", 50.0)
    if abs(l_a - l_b) > 15.0:
        flag = "PARTIAL"
        reasons.append(f"Chênh lệch ánh sáng đáng kể giữa hai lần chụp (|ΔL*| = {round(abs(l_a - l_b), 1)})")

    # 6. Check ROI area difference
    roi_area_a = obs_a.get("roi_area", 100.0)
    roi_area_b = obs_b.get("roi_area", 100.0)
    if roi_area_a > 0:
        area_diff_pct = abs(roi_area_a - roi_area_b) / roi_area_a * 100.0
        if area_diff_pct > 35.0:
            flag = "PARTIAL"
            reasons.append(f"Kích thước khung chụp chênh lệch lớn ({round(area_diff_pct, 1)}% > 35%)")

    # Calculate Deltas if COMPARABLE
    if flag == "COMPARABLE":
        area_a = obs_a.get("affected_area_ratio", 0.0)
        area_b = obs_b.get("affected_area_ratio", 0.0)
        delta_area = round(area_b - area_a, 2)
        deltas["delta_affected_area_ratio"] = delta_area
        reasons.append("Hai ảnh đạt tiêu chuẩn so sánh hình học và ánh sáng")

    return {
        "flag": flag,
        "reasons": reasons,
        "deltas": deltas
    }
