"""
pdf_export.py — Neutral PDF Generator for Medical Reports.
Produces valid PDF 1.4 documents containing:
- Neutral file name and header (NO disease name in header).
- Mandatory Medical Disclaimer Banner (Non-diagnostic).
- Provenance tracking tables.
- Similar conditions reference section with disclaimers.
Zero external C dependencies (pure Python).
"""
import io
import datetime

def generate_pdf_report(report_dict: dict) -> bytes:
    """Generate a clean, valid PDF 1.4 byte string for a medical observation report."""
    case_id = report_dict.get("case_id", "CASE-UNKNOWN")[:8]
    audience = report_dict.get("audience", "patient")
    generated_at = report_dict.get("generated_at", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))

    # Extract lines to render
    lines = [
        "DERMACARE AGENT - HO SO THEO DOI TIEN TRIEN DA",
        f"Ma ho so: {case_id}  |  Doi tuong: {audience}  |  Ngay tao: {generated_at}",
        "--------------------------------------------------------------------------------",
        "[CANH BAO QUAN TRONG / MEDICAL DISCLAIMER]",
        "BAN BAO CAO NAY KHONG PHAI CHAN DOAN Y KHOA.",
        "Cong cu chi dung de ho tro theo doi dien tien hinh anh ton thuong da va cung cap",
        "thong tin tham khao cho bac si chuyen khoa da lieu.",
        "Moi danh gia benh hoc va phac do dieu tri thuoc tham quyen cua bac si.",
        "--------------------------------------------------------------------------------",
        "",
        "1. CAC TINH TRANG DA CO BIEU HIEN TUONG DONG (THAM KHAO):",
        "(Duoc truy van tu co so kien thuc Vector DB 64 chieu, sap xep A-Z, KHONG ti le %)",
    ]

    sims = report_dict.get("similar_conditions", [])
    if sims:
        for it in sims[:5]:
            name_en = it.get("name_en", "")
            summary = it.get("summary", it.get("summary_vi", ""))
            lines.append(f"  * {name_en}: {summary[:70]}")
    else:
        lines.append("  (Chua ghi nhan tinh trang tuong dong phu hop)")

    lines.extend([
        "",
        "2. CHI SO DO LUONG HINH ANH (AI-MEASURED):",
        "  Thoi diem           Chi so                 Gia tri     Do tin cay   Nguon goc",
    ])

    ai_m = report_dict.get("ai_measurements", [])
    if ai_m:
        for m in ai_m[:6]:
            dt = m.get("captured_at", "")[:19]
            name = m.get("metric_name", "")[:20]
            val = f"{m.get('value', 0)} {m.get('unit', '')}"[:10]
            conf = f"{m.get('confidence', 0)}"[:5]
            lines.append(f"  {dt:<19} {name:<22} {val:<11} {conf:<11} [ai_measured]")
    else:
        lines.append("  (Chua co du lieu do hinh anh dat tieu chuan)")

    lines.extend([
        "",
        "3. NHAT KY TRIEU CHUNG TU KHAI (USER-REPORTED):",
    ])
    syms = report_dict.get("symptoms", [])
    if syms:
        for s in syms[:4]:
            dt = s.get("entered_at", "")[:19]
            ans = str(s.get("answers_summary", ""))[:45]
            lines.append(f"  {dt}: {ans} [user_reported]")
    else:
        lines.append("  (Chua co nhat ky trieu chung)")

    lines.extend([
        "",
        "--------------------------------------------------------------------------------",
        "Chung thuc nguon goc: Avalanche C-Chain Zero-PII Commitment",
        "DermaCare Agent - Privacy-Preserving Dermatology Tracking System",
        "--------------------------------------------------------------------------------"
    ])

    # Build PDF 1.4 stream
    stream_content = "BT\n/F1 10 Tf\n14 TL\n40 760 Td\n"
    for line in lines:
        # Escape parenthesis
        safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_content += f"({safe_line}) '\n"
    stream_content += "ET\n"
    stream_bytes = stream_content.encode("latin-1", errors="replace")

    # Assemble PDF objects
    objs = []
    # 1: Catalog
    objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # 2: Pages
    objs.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # 3: Page
    objs.append(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
    # 4: Stream
    objs.append(f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1") + stream_bytes + b"\nendstream\nendobj\n")
    # 5: Font
    objs.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for obj in objs:
        offsets.append(len(out))
        out.extend(obj)

    xref_offset = len(out)
    out.extend(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode("latin-1"))
    for off in offsets:
        out.extend(f"{off:010d} 00000 n \n".encode("latin-1"))
    out.extend(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1"))

    return bytes(out)
