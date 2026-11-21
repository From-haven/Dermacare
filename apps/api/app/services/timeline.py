"""
timeline.py — Longitudinal Timeline and Trend Generation.
Rules:
- Requires >= 3 COMPARABLE points to compute rolling trend.
- Neutral language: "chỉ số X tăng/giảm trong ảnh", NEVER "tốt lên/xấu đi/khỏi".
- Profile 'other' displays points but NEVER draws a trend line.
- Every metric has explicit provenance {ai_measured, user_reported, clinician_entered, synthetic}.
"""
from typing import List, Dict, Any

def compute_rolling_median(values: List[float], window: int = 3) -> List[float]:
    """Compute rolling median over window size 3."""
    res = []
    for i in range(len(values)):
        sub = values[max(0, i - window + 1) : i + 1]
        sorted_sub = sorted(sub)
        res.append(round(sorted_sub[len(sorted_sub) // 2], 2))
    return res

def generate_timeline(
    observations: List[Dict[str, Any]],
    profile_type: str = "other",
    metric_name: str = "affected_area_ratio"
) -> Dict[str, Any]:
    """Generate structured timeline data for charts and report."""
    points = []
    comparable_count = 0

    for obs in observations:
        m_val = obs.get("measurements", {}).get(metric_name)
        comp_flag = obs.get("comparison_flag", "COMPARABLE")
        if comp_flag == "COMPARABLE":
            comparable_count += 1

        points.append({
            "observation_id": obs.get("id"),
            "captured_at": obs.get("captured_at"),
            "value": m_val,
            "comparability": comp_flag,
            "provenance": obs.get("provenance", "ai_measured"),
            "notes": obs.get("notes", "")
        })

    # Sort chronological
    points.sort(key=lambda x: x["captured_at"])

    # Trend calculation
    trend_data = []
    trend_summary = ""
    can_draw_trend = (profile_type != "other" and comparable_count >= 3)

    if can_draw_trend:
        comparable_vals = [p["value"] for p in points if p["comparability"] == "COMPARABLE" and p["value"] is not None]
        if len(comparable_vals) >= 3:
            rolling_med = compute_rolling_median(comparable_vals, 3)
            idx = 0
            for p in points:
                if p["comparability"] == "COMPARABLE" and p["value"] is not None:
                    p["trend_value"] = rolling_med[idx]
                    idx += 1
                else:
                    p["trend_value"] = None

            first_val = rolling_med[0]
            last_val = rolling_med[-1]
            diff = round(last_val - first_val, 2)
            if diff > 1.0:
                trend_summary = f"Chỉ số {metric_name} có xu hướng tăng ({diff:+}%) trong các ảnh chụp"
            elif diff < -1.0:
                trend_summary = f"Chỉ số {metric_name} có xu hướng giảm ({diff:+}%) trong các ảnh chụp"
            else:
                trend_summary = f"Chỉ số {metric_name} duy trì ổn định trong các ảnh chụp"
    elif profile_type == "other":
        trend_summary = "Hồ sơ tình trạng chưa rõ (other): hiển thị từng điểm đo riêng lẻ, không vẽ đường xu hướng"
    else:
        trend_summary = f"Chưa đủ 3 điểm chụp tương thích để tính toán xu hướng (hiện có {comparable_count} điểm)"

    return {
        "metric_name": metric_name,
        "profile_type": profile_type,
        "can_draw_trend": can_draw_trend,
        "trend_summary": trend_summary,
        "points": points
    }
