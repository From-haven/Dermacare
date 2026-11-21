import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def create_document(output_path):
    doc = docx.Document()

    # Page Margins: 1 inch (2.54 cm) all around
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # Styles
    # Normal style
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(30, 41, 59) # Slate 800

    # Helper function to add styled headings
    def add_custom_heading(text, level, space_before=14, space_after=6):
        h = doc.add_heading(text, level=level)
        h.paragraph_format.space_before = Pt(space_before)
        h.paragraph_format.space_after = Pt(space_after)
        h.paragraph_format.keep_with_next = True
        run = h.runs[0]
        if level == 1:
            run.font.name = 'Calibri'
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = RGBColor(2, 132, 199) # Primary Blue #0284c7
        elif level == 2:
            run.font.name = 'Calibri'
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = RGBColor(15, 23, 42) # Slate 900
        elif level == 3:
            run.font.name = 'Calibri'
            run.font.size = Pt(11.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(3, 105, 161) # Deep Blue
        return h

    # Helper for shaded callout box
    def add_callout(text, bold_prefix="", bg_color="F0F9FF", border_color="0284C7"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.5)

        # Background color
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_color}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

        # Left border only
        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        ''')
        cell._tc.get_or_add_tcPr().append(borders)

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.15)
        p.paragraph_format.right_indent = Inches(0.15)

        if bold_prefix:
            r_bold = p.add_run(bold_prefix + " ")
            r_bold.font.bold = True
            r_bold.font.color.rgb = RGBColor(3, 105, 161)
        r_text = p.add_run(text)
        r_text.font.size = Pt(10.5)
        r_text.font.italic = True
        r_text.font.color.rgb = RGBColor(30, 41, 59)

        # Empty paragraph after table for spacing
        p_after = doc.add_paragraph()
        p_after.paragraph_format.space_before = Pt(0)
        p_after.paragraph_format.space_after = Pt(4)

    # ---------------- DOCUMENT HEADER ----------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(10)
    title_p.paragraph_format.space_after = Pt(4)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = title_p.add_run("ĐỒ ÁN DERMACARE AGENT")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(20)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(2, 132, 199)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_before = Pt(0)
    sub_p.paragraph_format.space_after = Pt(16)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = sub_p.add_run("BÁO CÁO PHÂN TÍCH: Ý TƯỞNG CỐT LÕI, THÀNH PHẦN CỐT LÕI & VAI TRÒ CỦA HỆ THỐNG AVALANCHE (BLOCKCHAIN)")
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(12)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    add_callout(
        "DermaCare Agent được định vị là công cụ y tế hỗ trợ theo dõi tiến triển tổn thương da liễu cá nhân khách quan, "
        "bảo tồn quyền riêng tư tối đa và neo giữ bằng chứng kiểm toán độc lập trên mạng Avalanche C-Chain. "
        "Hệ thống tuyệt đối không đưa ra kết luận chẩn đoán khẳng định y khoa.",
        bold_prefix="TỔNG QUAN ĐỊNH VỊ:"
    )

    # ---------------- PHẦN 1: Ý TƯỞNG CỐT LÕI ----------------
    add_custom_heading("1. Ý TƯỞNG CỐT LÕI (CORE IDEA)", level=1)

    p1 = doc.add_paragraph()
    p1.add_run("Ý tưởng cốt lõi của đồ án xuất phát từ việc giải quyết nghịch lý lớn nhất của các ứng dụng trí tuệ nhân tạo (AI) trong lĩnh vực da liễu hiện nay: ")
    r_em = p1.add_run('"Ảo giác chẩn đoán" (Diagnostic Hallucination) và "Xâm phạm quyền riêng tư" (Privacy Breach).')
    r_em.font.bold = True

    add_custom_heading("1.1. Thực trạng & Rủi ro của các ứng dụng hiện hành", level=2)
    
    b1 = doc.add_paragraph(style='List Bullet')
    b1.add_run("Chẩn đoán vượt quyền hạn y tế: ").font.bold = True
    b1.add_run("Phần lớn các app hiện nay cố gắng thay thế vai trò bác sĩ, đưa ra kết luận khẳng định như \"Bạn có 85% mắc bệnh ung thư da\", \"Tổn thương này lành tính 90%\". Điều này tạo ra cảm giác an tâm giả tạo hoặc gây hoang mang cực độ cho bệnh nhân, dẫn đến bỏ lỡ thời điểm vàng điều trị.")

    b2 = doc.add_paragraph(style='List Bullet')
    b2.add_run("Xâm phạm quyền riêng tư nghiêm trọng: ").font.bold = True
    b2.add_run("Bệnh nhân phải tải hình ảnh các vùng da nhạy cảm (mặt, ngực, vùng bẹn) và tọa độ GPS định vị chính xác lên máy chủ trung tâm mà không có cơ chế mã hóa đầu-cuối, vi phạm nghiêm trọng Luật Bảo vệ Dữ liệu Cá nhân và tiêu chuẩn HIPAA/GDPR.")

    b3 = doc.add_paragraph(style='List Bullet')
    b3.add_run("Thiếu cơ sở khoa học cho theo dõi tiến triển: ").font.bold = True
    b3.add_run("Bệnh nhân chụp ảnh ở các góc chụp, khoảng cách và điều kiện ánh sáng khác nhau nhưng các ứng dụng vẫn so sánh và tự ý phán đoán \"đỡ hơn\" hay \"nặng hơn\" một cách vô căn cứ.")

    add_custom_heading("1.2. Giải pháp cốt lõi của DermaCare Agent", level=2)
    
    s1 = doc.add_paragraph(style='List Bullet')
    s1.add_run("Phi chẩn đoán (Non-diagnostic): ").font.bold = True
    s1.add_run("DermaCare Agent khẳng định ranh giới rõ ràng: KHÔNG chẩn đoán bệnh, KHÔNG kê đơn thuốc, KHÔNG đưa ra điểm số tổng \"Skin Score\", và KHÔNG hiển thị tỷ lệ phần trăm (%). Mọi thông tin chỉ mang tính đối sánh tham khảo y văn.")

    s2 = doc.add_paragraph(style='List Bullet')
    s2.add_run("Công cụ theo dõi tiến triển khách quan (Longitudinal Tracking): ").font.bold = True
    s2.add_run("Thay vì phán đoán bệnh, hệ thống đóng vai trò như một \"thước đo điện tử\" giúp người bệnh ghi nhận diễn tiến khách quan (diện tích tổn thương, độ viêm đỏ bán định lượng) qua chuỗi thời gian nhiều tuần/nhiều tháng.")

    s3 = doc.add_paragraph(style='List Bullet')
    s3.add_run("Bảo tồn quyền riêng tư tối đa (Privacy-First): ").font.bold = True
    s3.add_run("Người dùng nắm toàn quyền quyết định dữ liệu: Tọa độ GPS không bao giờ lưu DB; 100% EXIF ảnh bị tước bỏ; ảnh được mã hóa envelope AES-256-GCM; chỉ bác sĩ được bệnh nhân cấp phép mới được mở ảnh trong 60 giây.")

    # ---------------- PHẦN 2: THÀNH PHẦN CỐT LÕI ----------------
    add_custom_heading("2. CÁC THÀNH PHẦN CỐT LÕI CỦA HỆ THỐNG (CORE ENGINE)", level=1)

    p_core = doc.add_paragraph()
    p_core.add_run("Hệ sinh thái kỹ thuật của DermaCare Agent được vận hành bởi 4 trụ cột cốt lõi phối hợp chặt chẽ:")

    add_custom_heading("2.1. Cổng kiểm soát chất lượng hình ảnh y tế (Quality Gate)", level=2)
    p_qg = doc.add_paragraph()
    p_qg.add_run("Trước khi đưa vào đo đạc hoặc đối sánh, ảnh chụp bắt buộc phải vượt qua bộ lọc chất lượng tự động: ")
    p_qg.add_run("Độ nét phương sai Laplacian (≥ 100), Độ phơi sáng trung bình (50 ≤ luminance ≤ 205), Tỷ lệ chói lóa (< 10%), và Độ phân giải tối thiểu. ")
    p_qg.add_run("Nếu ảnh bị mờ hoặc tối, hệ thống lập tức gắn nhãn ")
    r_retake = p_qg.add_run("RETAKE (Cần chụp lại)")
    r_retake.font.bold = True
    r_retake.font.color.rgb = RGBColor(185, 28, 28)
    p_qg.add_run(" kèm chỉ dẫn cụ thể, tuyệt đối không phân tích trên ảnh kém chất lượng.")

    add_custom_heading("2.2. Bộ đánh giá tính tương thích so sánh (Comparability Evaluator)", level=2)
    p_comp = doc.add_paragraph()
    p_comp.add_run("Để đảm bảo nguyên tắc ")
    p_comp.add_run('"không so sánh táo với cam", ').font.bold = True
    p_comp.add_run("hệ thống kiểm tra tính tương đồng giữa hai lần chụp: cùng vị trí giải phẫu (body site), cùng góc chụp và độ chênh lệch ánh sáng cho phép. ")
    p_comp.add_run("Nếu không tương thích, hệ thống gắn cờ ")
    r_notcomp = p_comp.add_run("NOT_COMPARABLE")
    r_notcomp.font.bold = True
    p_comp.add_run(" và ngừng vẽ biểu đồ chênh lệch, ngăn ngừa tuyệt đối việc ngộ nhận về diễn tiến bệnh.")

    add_custom_heading("2.3. Đo lường Heuristic & Tra cứu Vector DB 64 chiều (fv-1)", level=2)
    p_vec = doc.add_paragraph()
    p_vec.add_run("Hệ thống trích xuất chỉ số viêm đỏ bán định lượng trên kênh màu LAB a* (thuật toán Otsu thích ứng kết hợp median/MAD) và tỷ lệ diện tích tổn thương. ")
    p_vec.add_run("Dữ liệu hình ảnh kết hợp cùng các câu trả lời triệu chứng tạo thành vector đặc trưng 64 chiều (")
    p_vec.add_run("fv-1").font.bold = True
    p_vec.add_run("), đối sánh Cosine Similarity trên Cơ sở tri thức 20 bệnh y văn chuẩn (Phụ lục B). Danh sách kết quả được ")
    p_vec.add_run("sắp xếp theo bảng chữ cái, không có %, kèm tuyên bố giới hạn bắt buộc.").font.bold = True

    add_custom_heading("2.4. Bộ định tuyến an toàn y học (Safety Router - 21 quy tắc tất định)", level=2)
    p_safe = doc.add_paragraph()
    p_safe.add_run("Chạy hoàn toàn độc lập với AI theo các quy tắc tất định nghiêm ngặt. Khi phát hiện các dấu hiệu cảnh báo đỏ nguy cấp (sốc phản vệ, hội chứng Stevens-Johnson, vết loét hoại tử, sốt cao kèm ban lan nhanh), hệ thống ")
    p_safe.add_run("ngắt luồng ngay lập tức, không trả về danh sách bệnh tham khảo và hướng dẫn người bệnh gọi ngay Cấp cứu 115.").font.bold = True

    # ---------------- PHẦN 3: VAI TRÒ CỦA AVALANCHE BLOCKCHAIN ----------------
    add_custom_heading("3. HỆ THỐNG AVALANCHE (BLOCKCHAIN) ĐÓNG VAI TRÒ GÌ?", level=1)

    add_callout(
        "Câu hỏi hội đồng thường đặt ra: \"Tại sao lại cần Blockchain ở đây? Có phải vẽ công nghệ ra để lấy điểm không?\"\n"
        "Câu trả lời: Blockchain trong DermaCare Agent không dùng để lưu trữ dữ liệu y tế, mà giải quyết 3 bài toán sống còn: "
        "Tính minh bạch không thể chối cãi (Non-repudiation), Kiểm toán chống sửa đổi (Tamper-evident audit trail), và Thanh toán dịch vụ y tế minh bạch.",
        bold_prefix="BẢN CHẤT KỸ THUẬT:"
    )

    add_custom_heading("3.1. Quản trị Vòng đời Cấp & Thu hồi Quyền Truy Cập (Decentralized Consent Lifecycle)", level=2)
    p_role1 = doc.add_paragraph()
    p_role1.add_run("• Vấn đề thực tế: ").font.bold = True
    p_role1.add_run("Khi bệnh nhân gửi hồ sơ bệnh án cho một cơ sở y tế trên máy chủ tập trung (Centralized Database), bệnh nhân không có cách nào kiểm chứng được phòng khám có tiếp tục lén lút truy cập dữ liệu của mình sau khi đợt khám kết thúc hay không.")
    
    p_role1_sol = doc.add_paragraph()
    p_role1_sol.add_run("• Giải pháp Avalanche: ").font.bold = True
    p_role1_sol.add_run("Hợp đồng thông minh ")
    p_role1_sol.add_run("ConsentRegistry.sol").font.bold = True
    p_role1_sol.add_run(" quản lý trạng thái ủy quyền bằng chữ ký số EIP-712. Bệnh nhân thiết lập thời hạn rõ ràng (7, 14, 30 ngày). ")
    p_role1_sol.add_run("Đặc biệt, khi bệnh nhân bấm \"Thu hồi\" (Revoke), trạng thái thu hồi được ghi vĩnh viễn lên Avalanche C-Chain. Máy chủ Backend lập tức từ chối quyền truy cập của bác sĩ (HTTP 403 Forbidden). Bác sĩ hoặc phòng khám không thể chối cãi hoặc gian lận quyền xem hồ sơ.")

    add_custom_heading("3.2. Neo Gốc Kiểm Toán Minh Bạch Chống Sửa Đổi (Merkle Audit Root Anchoring)", level=2)
    p_role2 = doc.add_paragraph()
    p_role2.add_run("• Vấn đề thực tế: ").font.bold = True
    p_role2.add_run("Máy chủ trung tâm của bệnh viện hoặc công ty công nghệ hoàn toàn có thể bị quản trị viên can thiệp, xóa log truy cập trái phép hoặc chỉnh sửa thời gian nhằm trốn tránh trách nhiệm khi xảy ra rò rỉ dữ liệu y tế.")

    p_role2_sol = doc.add_paragraph()
    p_role2_sol.add_run("• Giải pháp Avalanche: ").font.bold = True
    p_role2_sol.add_run("Mọi sự kiện quan trọng trong hệ thống (bác sĩ xem ảnh bằng token 60s, ảnh vượt qua Quality Gate, cập nhật chỉ số) được gom lô định kỳ (batching) và tính toán thành một ")
    p_role2_sol.add_run("Cây Merkle (Merkle Tree). ").font.bold = True
    p_role2_sol.add_run("Gốc Merkle (bytes32 root) được neo định kỳ lên Avalanche thông qua hàm ")
    p_role2_sol.add_run("anchorAudit(bytes32 root, uint256 batchId). ").font.bold = True
    p_role2_sol.add_run("Nhờ tính bất biến (immutability) của blockchain, máy chủ không thể chỉnh sửa lén lút nhật ký kiểm toán. Bệnh nhân hoặc cơ quan thanh tra y tế có thể dùng bằng chứng Merkle Proof để đối soát bất cứ lúc nào.")

    add_custom_heading("3.3. Thanh Toán & Xác Thực Đối Tác Minh Bạch (Verified Partner Settlement)", level=2)
    p_role3 = doc.add_paragraph()
    p_role3.add_run("• Vấn đề thực tế: ").font.bold = True
    p_role3.add_run("Để phòng khám xuất hiện ưu tiên trên bản đồ GPS và nhận hồ sơ trực tuyến từ người bệnh, cần cơ chế chứng minh quyền đối tác rõ ràng, tránh việc tự ý gán nhãn đối tác giả mạo trên cơ sở dữ liệu nội bộ.")

    p_role3_sol = doc.add_paragraph()
    p_role3_sol.add_run("• Giải pháp Avalanche: ").font.bold = True
    p_role3_sol.add_run("Thông qua hợp đồng ")
    p_role3_sol.add_run("TestSettlement.sol").font.bold = True
    p_role3_sol.add_run(" và token thử nghiệm ")
    p_role3_sol.add_run("DermaTestToken.sol (DTT), ").font.bold = True
    p_role3_sol.add_run("phòng khám thực hiện giao dịch thanh toán mua gói đối tác trên chuỗi. ")
    p_role3_sol.add_run("Logic hệ thống chỉ kích hoạt thời hạn đối tác (partner_until) khi giao dịch đạt trạng thái ")
    p_role3_sol.add_run("CONFIRMED. ").font.bold = True
    p_role3_sol.add_run("Nếu giao dịch thất bại (FAILED), hệ thống tuyệt đối không kích hoạt, loại trừ gian lận thương mại.")

    # ---------------- PHẦN 4: NGUYÊN TẮC ZERO-PII ----------------
    add_custom_heading("4. NGUYÊN TẮC SỐNG CÒN: ZERO-PII TRÊN BLOCKCHAIN", level=1)

    p_zero = doc.add_paragraph()
    p_zero.add_run("Nhiều đồ án blockchain y tế mắc sai lầm nghiêm trọng khi lưu trữ hồ sơ, hình ảnh hoặc thông tin bệnh nhân lên blockchain. Đây là hành vi vi phạm nghiêm trọng luật bảo vệ dữ liệu cá nhân (GDPR) vì dữ liệu trên blockchain không thể xóa bỏ (\"Quyền được lãng quên\").")

    p_zero_sol = doc.add_paragraph()
    p_zero_sol.add_run("DermaCare Agent tuân thủ nghiêm ngặt nguyên tắc ")
    p_zero_sol.add_run("Zero-PII On-Chain: ").font.bold = True
    p_zero_sol.add_run("Blockchain ")
    p_zero_sol.add_run("TUYỆT ĐỐI KHÔNG ").font.bold = True
    p_zero_sol.add_run("lưu email, họ tên, số điện thoại, ảnh tổn thương, triệu chứng, tên bệnh, hay tọa độ GPS.")

    add_callout(
        "Dữ liệu duy nhất gửi lên hợp đồng thông minh là Cam kết Mật mã Ngẫu nhiên:\n"
        "Commitment Hash = SHA256(CSPRNG_Salt_16_bytes || patient_id || clinic_id)\n\n"
        "Người ngoài nhìn vào Avalanche C-Chain Explorer chỉ thấy chuỗi băm ngẫu nhiên 0x89ab...45ef, "
        "hoàn toàn không chứa bất kỳ entropy nào để có thể giải mã ngược ra danh tính của người bệnh.",
        bold_prefix="CÔNG THỨC CAM KẾT MẬT MÃ:"
    )

    # ---------------- PHẦN 5: BẢNG TỔNG KẾT SO SÁNH ----------------
    add_custom_heading("5. BẢNG TỔNG KẾT GIÁ TRỊ CỐT LÕI", level=1)

    table = doc.add_table(rows=5, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = [Inches(1.8), Inches(2.3), Inches(2.4)]
    headers = ["Trụ cột", "Giải pháp thông thường (Thị trường)", "Giải pháp DermaCare Agent"]

    # Header row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].width = col_widths[i]
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="0284C7"/>')
        hdr_cells[i]._tc.get_or_add_tcPr().append(shd)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(title)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ("Mục tiêu ứng dụng", "Chẩn đoán bệnh khẳng định thay bác sĩ; đưa ra xác suất % vô căn cứ.", "Phi chẩn đoán; công cụ theo dõi tiến triển khách quan; tra cứu đối sánh y văn."),
        ("Chất lượng ảnh", "Người dùng gửi ảnh nào cũng nhận; so sánh bừa bãi giữa các lần chụp.", "Quality Gate đo độ nét/sáng; Comparability Evaluator từ chối so sánh khi sai góc."),
        ("Quyền riêng tư", "Lưu GPS chính xác và ảnh thô lên server; nguy cơ rò rỉ dữ liệu cao.", "Xóa sạch EXIF; mã hóa AES-256-GCM; tọa độ GPS không bao giờ lưu DB; token ảnh 60s."),
        ("Vai trò Blockchain", "Lưu dữ liệu bệnh án lên chuỗi (sai lầm vi phạm GDPR); hoặc không dùng.", "Zero-PII On-Chain; quản trị quyền truy cập EIP-712; neo gốc Merkle chống sửa log.")
    ]

    for row_idx, row_data in enumerate(data, start=1):
        row_cells = table.rows[row_idx].cells
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(row_data):
            row_cells[col_idx].width = col_widths[col_idx]
            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg}"/>')
            row_cells[col_idx]._tc.get_or_add_tcPr().append(shd)
            p = row_cells[col_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.font.bold = True
                r.font.color.rgb = RGBColor(15, 23, 42)

    # Save document
    doc.save(output_path)
    print(f"Document saved successfully to: {output_path}")

if __name__ == "__main__":
    create_document("DermaCare_Y_Tuong_Cot_Loi_Va_Blockchain.docx")
