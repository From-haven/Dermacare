"""
reports.py — Medical Report Generator (HTML/PDF/JSON).
Rules (Section 14 Master Spec):
- Header: neutral file name, NO disease name in header.
- Banner: "Không phải chẩn đoán / Not a medical diagnosis".
- 4 Provenance tables: AI-measured / User-reported / Clinician-entered / Synthetic.
- "Các tình trạng có biểu hiện tương đồng (tham khảo)" section with disclaimer (only section allowed to state condition names).
- Timeline of individual metrics (NO skin score).
- Missing data list & non-comparable images list with reasons.
- Supports both patient and clinician audiences.
"""
import json
import datetime
from app.core.db import get_db

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Báo cáo theo dõi biểu hiện da - DermaCare Agent</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #1f2937; margin: 40px; background: #fff; }
  .disclaimer-banner { background: #fee2e2; border: 2px solid #ef4444; border-radius: 8px; padding: 16px; margin-bottom: 24px; color: #991b1b; font-weight: 600; }
  .header { border-bottom: 2px solid #e5e7eb; padding-bottom: 16px; margin-bottom: 24px; }
  .section-title { font-size: 18px; font-weight: 700; color: #111827; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-top: 24px; margin-bottom: 12px; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px; }
  th, td { border: 1px solid #d1d5db; padding: 8px 12px; text-align: left; }
  th { background-color: #f3f4f6; color: #374151; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 12px; font-weight: 600; }
  .badge-ai { background: #dbeafe; color: #1e40af; }
  .badge-user { background: #fef3c7; color: #92400e; }
  .badge-clinician { background: #d1fae5; color: #065f46; }
  .badge-synthetic { background: #f3e8ff; color: #6b21a8; }
  .footer { margin-top: 40px; font-size: 12px; color: #6b7280; text-align: center; border-top: 1px solid #e5e7eb; padding-top: 16px; }
</style>
</head>
<body>

<div class="disclaimer-banner">
  ⚠️ BẢN BÁO CÁO THEO DÕI BIỂU HIỆN DA — KHÔNG PHẢI CHẨN ĐOÁN Y KHOA<br>
  <span style="font-size: 13px; font-weight: normal;">
    Tài liệu này được tạo tự động bởi DermaCare Agent phục vụ việc đối chiếu và cung cấp thông tin tham khảo cho bác sĩ da liễu.
    Mọi đánh giá bệnh học và phác đồ điều trị thuộc thẩm quyền của nhân viên y tế có chứng chỉ hành nghề.
  </span>
</div>

<div class="header">
  <h2>HỒ SƠ THEO DÕI BIỂU HIỆN DA</h2>
  <p><strong>Mã hồ sơ:</strong> {{case_id}} | <strong>Vùng cơ thể:</strong> {{case_body_site}} | <strong>Profile:</strong> {{case_profile_type}}</p>
  <p><strong>Ngày tạo báo cáo:</strong> {{generated_at}} | <strong>Đối tượng:</strong> {{audience}}</p>
</div>

<div class="section-title">1. Các tình trạng da có biểu hiện tương đồng (chỉ để tham khảo)</div>
<p style="font-size: 13px; font-style: italic; color: #4b5563;">
  Danh sách dưới đây được truy vấn từ cơ sở dữ liệu kiến thức tham khảo dựa trên đặc trưng hình ảnh và triệu chứng đã khai báo.
  Danh sách này không phải chẩn đoán và không biểu thị phần trăm (%) khả năng mắc bệnh.
</p>
<table>
  <thead>
    <tr>
      <th>Tên tình trạng (tham khảo)</th>
      <th>Tên tiếng Anh</th>
      <th>Đặc điểm biểu hiện điển hình</th>
      <th>Trạng thái thẩm định</th>
    </tr>
  </thead>
  <tbody>
    {{similar_conditions_rows}}
  </tbody>
</table>

<div class="section-title">2. Số liệu phân tích hình ảnh (AI-Measured)</div>
<table>
  <thead>
    <tr>
      <th>Thời điểm ghi nhận</th>
      <th>Chỉ số</th>
      <th>Giá trị đo</th>
      <th>Độ tin cậy</th>
      <th>Phiên bản mô hình</th>
      <th>Nguồn gốc (Provenance)</th>
    </tr>
  </thead>
  <tbody>
    {{ai_measurements_rows}}
  </tbody>
</table>

<div class="section-title">3. Nhật ký triệu chứng tự khai (User-Reported)</div>
<table>
  <thead>
    <tr>
      <th>Ngày khai báo</th>
      <th>Triệu chứng ghi nhận</th>
      <th>Khởi phát</th>
      <th>Nguồn gốc (Provenance)</th>
    </tr>
  </thead>
  <tbody>
    {{symptoms_rows}}
  </tbody>
</table>

<div class="section-title">4. Đánh giá chuyên môn của Bác sĩ (Clinician-Entered)</div>
<table>
  <thead>
    <tr>
      <th>Thời điểm</th>
      <th>Bác sĩ</th>
      <th>Điểm lâm sàng</th>
      <th>Ghi chú chuyên môn</th>
      <th>Nguồn gốc (Provenance)</th>
    </tr>
  </thead>
  <tbody>
    {{clinician_reviews_rows}}
  </tbody>
</table>

<div class="section-title">5. Các ảnh không thể so sánh và dữ liệu còn thiếu</div>
<p style="font-size: 13px; color: #4b5563;">
  Danh sách ghi nhận các lần chụp ảnh không đủ điều kiện so sánh tiến triển (do lệch góc, lệch ánh sáng hoặc chất lượng không đạt):
</p>
<ul>
  {{non_comparable_items}}
</ul>

<div class="footer">
  DermaCare Agent Platform • Báo cáo mã hoá riêng tư • Không lưu toạ độ GPS • Bằng chứng xác thực Avalanche Fuji
</div>

</body>
</html>
"""

def generate_case_report(case_id: str, audience: str = "patient") -> dict:
    """Generate structured JSON report and HTML content for case."""
    db = get_db()
    case = db.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if not case:
        raise ValueError("Case not found")

    case_dict = dict(case)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    # 1. Fetch similar conditions from latest observation
    obs = db.execute(
        "SELECT id FROM observations WHERE case_id = ? ORDER BY captured_at DESC LIMIT 1",
        (case_id,)
    ).fetchone()

    similar_conditions = []
    if obs:
        sim_row = db.execute(
            "SELECT results FROM similar_condition_results WHERE observation_id = ? ORDER BY created_at DESC LIMIT 1",
            (obs["id"],)
        ).fetchone()
        if sim_row and sim_row["results"]:
            items = json.loads(sim_row["results"])
            for it in items:
                cond = db.execute("SELECT name_vi, name_en, summary_vi FROM knowledge_conditions WHERE slug = ?", (it["slug"],)).fetchone()
                if cond:
                    similar_conditions.append({
                        "name_vi": cond["name_vi"],
                        "name_en": cond["name_en"],
                        "summary": cond["summary_vi"]
                    })

    # 2. Fetch AI measurements
    measures = db.execute(
        """
        SELECT vm.*, o.captured_at
        FROM visual_measurements vm
        JOIN observations o ON vm.observation_id = o.id
        WHERE o.case_id = ?
        ORDER BY o.captured_at ASC
        """,
        (case_id,)
    ).fetchall()
    ai_measurements = [dict(m) for m in measures]

    # 3. Fetch symptoms
    sym_rows = db.execute("SELECT * FROM symptom_entries WHERE case_id = ? ORDER BY entered_at ASC", (case_id,)).fetchall()
    symptoms = []
    for s in sym_rows:
        ans = json.loads(s["answers"]) if isinstance(s["answers"], str) else s["answers"]
        summary_parts = [f"{k}: {v}" for k, v in ans.items() if v and v != "none" and v is not False]
        symptoms.append({
            "entered_at": s["entered_at"],
            "answers_summary": ", ".join(summary_parts[:5]) if summary_parts else "Bình thường",
            "onset": ans.get("onset", "Không rõ")
        })

    # 4. Fetch clinician reviews
    rev_rows = db.execute(
        """
        SELECT cr.*, u.display_name as clinician_name
        FROM clinician_reviews cr
        JOIN users u ON cr.clinician_id = u.id
        WHERE cr.case_id = ?
        ORDER BY cr.created_at ASC
        """,
        (case_id,)
    ).fetchall()
    clinician_reviews = [dict(r) for r in rev_rows]

    # 5. Non-comparable items
    comp_rows = db.execute("SELECT * FROM comparisons WHERE case_id = ? AND flag != 'COMPARABLE'", (case_id,)).fetchall()
    non_comparable = []
    for c in comp_rows:
        reasons = json.loads(c["reasons"]) if isinstance(c["reasons"], str) else c["reasons"]
        non_comparable.append({
            "captured_at": c["created_at"],
            "reason": "; ".join(reasons)
        })

    # Render HTML Rows
    # Similar conditions rows
    if similar_conditions:
        sim_rows_html = "".join(
            f"<tr><td><strong>{it['name_vi']}</strong></td><td>{it['name_en']}</td><td>{it['summary']}</td><td><span class='badge badge-synthetic'>synthetic (draft)</span></td></tr>\n"
            for it in similar_conditions
        )
    else:
        sim_rows_html = "<tr><td colspan='4' style='text-align: center; color: #6b7280;'>Chưa ghi nhận tình trạng tương đồng phù hợp.</td></tr>"

    # AI measurements rows
    if ai_measurements:
        ai_rows_html = "".join(
            f"<tr><td>{m.get('captured_at', '')}</td><td>{m.get('metric_name', '')}</td><td>{m.get('value', '')} {m.get('unit', '')}</td><td>{m.get('confidence', '')}</td><td>{m.get('model_version', '')}</td><td><span class='badge badge-ai'>ai_measured</span></td></tr>\n"
            for m in ai_measurements
        )
    else:
        ai_rows_html = "<tr><td colspan='6' style='text-align: center; color: #6b7280;'>Chưa có dữ liệu đo hình ảnh đạt tiêu chuẩn (<span class='badge badge-ai'>ai_measured</span>).</td></tr>"

    # Symptoms rows
    if symptoms:
        sym_rows_html = "".join(
            f"<tr><td>{s['entered_at']}</td><td>{s['answers_summary']}</td><td>{s['onset']}</td><td><span class='badge badge-user'>user_reported</span></td></tr>\n"
            for s in symptoms
        )
    else:
        sym_rows_html = "<tr><td colspan='4' style='text-align: center; color: #6b7280;'>Chưa có nhật ký triệu chứng (<span class='badge badge-user'>user_reported</span>).</td></tr>"

    # Clinician reviews rows
    if clinician_reviews:
        cr_rows_html = "".join(
            f"<tr><td>{r['created_at']}</td><td>{r.get('clinician_name', 'Bác sĩ')}</td><td>{r.get('clinician_scores', '')}</td><td>{r.get('note', '')}</td><td><span class='badge badge-clinician'>clinician_entered</span></td></tr>\n"
            for r in clinician_reviews
        )
    else:
        cr_rows_html = "<tr><td colspan='5' style='text-align: center; color: #6b7280;'>Chưa có ghi nhận đánh giá từ bác sĩ (<span class='badge badge-clinician'>clinician_entered</span>).</td></tr>"

    # Non-comparable list items
    if non_comparable:
        nc_items_html = "".join(f"<li><strong>Lần chụp {nc['captured_at']}:</strong> {nc['reason']}</li>\n" for nc in non_comparable)
    else:
        nc_items_html = "<li>Tất cả các lần chụp đạt tiêu chuẩn tương thích.</li>"

    html = REPORT_TEMPLATE
    html = html.replace("{{case_id}}", case_dict["id"][:8])
    html = html.replace("{{case_body_site}}", case_dict["body_site"])
    html = html.replace("{{case_profile_type}}", case_dict["profile_type"])
    html = html.replace("{{generated_at}}", now)
    html = html.replace("{{audience}}", audience)
    html = html.replace("{{similar_conditions_rows}}", sim_rows_html)
    html = html.replace("{{ai_measurements_rows}}", ai_rows_html)
    html = html.replace("{{symptoms_rows}}", sym_rows_html)
    html = html.replace("{{clinician_reviews_rows}}", cr_rows_html)
    html = html.replace("{{non_comparable_items}}", nc_items_html)

    return {
        "case_id": case_id,
        "audience": audience,
        "generated_at": now,
        "similar_conditions": similar_conditions,
        "ai_measurements": ai_measurements,
        "symptoms": symptoms,
        "non_comparable": non_comparable,
        "html_content": html
    }
