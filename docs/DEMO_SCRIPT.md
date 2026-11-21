# DermaCare Agent — Kịch Bản Trình Diễn Trực Tiếp (Live Demo Script)

Kịch bản 5–7 phút dành cho buổi thuyết trình và chấm thi sản phẩm DermaCare Agent.

---

## Mở Đầu (30 giây) — Giới Thiệu & Bài Toán
- **Lời dẫn:** "Kính thưa Ban Giám Khảo, hiện nay các ứng dụng AI chẩn đoán da liễu thường gặp 3 rào cản nghiêm trọng: chẩn đoán khẳng định vượt quyền hạn y tế, rò rỉ dữ liệu hình ảnh nhạy cảm và vị trí của người dùng, và thiếu minh bạch về nguồn gốc dữ liệu. DermaCare Agent được phát triển để giải quyết triệt để bài toán này."
- **Hành động:** Mở trang chủ `http://localhost:8000/`. Chỉ vào banner cố định màu vàng: *"LƯU Ý QUAN TRỌNG: Công cụ tham khảo & theo dõi tiến triển tổn thương da liễu, không phải chẩn đoán y khoa."*

---

## Phần 1 (2 phút) — Trải Nghiệm Bệnh Nhân & Luồng Tra Cứu 6 Bước (`/start`)
1. **Bước 1 — Sơ đồ giải phẫu (Body Map):**
   - Nhấp chọn vùng **Mặt (Face)** hoặc **Cánh tay (Arms)** trên SVG Body Map. Nhấn Tiếp tục.
2. **Bước 2 — Triệu chứng & Cảnh báo đỏ:**
   - Chọn thời gian khởi phát: 1 đến 4 tuần. Đánh dấu cảm giác ngứa, khô da.
   - Nhấn mạnh: Nếu tích vào các dấu hiệu Red Flags (chảy máu, sốt cao), hệ thống sẽ lập tức hiển thị cảnh báo khuyến nghị cấp cứu khẩn cấp mà không đưa ra phán đoán bừa bãi.
3. **Bước 3 — Cổng kiểm tra chất lượng ảnh (Quality Gate):**
   - Thử tải một ảnh mờ hoặc ảnh tối: Hệ thống gắn nhãn **CẦN CHỤP LẠI (RETAKE)** kèm lý do cụ thể (Laplacian < 100).
   - Nhấn nút "Sử dụng ảnh mẫu sắc nét": Quality Gate chuyển sang **ĐẠT TIÊU CHUẨN (PASS)** kèm huy hiệu `AI Measured`.
4. **Bước 4 — Bảng tham khảo tình trạng tương đồng (`SimilarConditionsPanel`):**
   - Chỉ cho Ban Giám Khảo thấy: Danh sách hiển thị theo bảng chữ cái. **Hoàn toàn không có phần trăm (%) xác suất**, không chấm điểm nặng nhẹ, có tuyên bố giới hạn y khoa bắt buộc.
5. **Bước 5 — Tìm cơ sở Da liễu gần nhất (Privacy GPS):**
   - Hệ thống hiển thị các cơ sở chuyên khoa. Cơ sở **Verified Partner** được xếp đầu tiên với nút *"Gửi hồ sơ & Tư vấn ngay"*. Nhấn mạnh: Tọa độ GPS của người dùng bị xóa ngay sau khi tính khoảng cách.
6. **Bước 6 — Ủy quyền chia sẻ (Avalanche Blockchain):**
   - Chọn thời hạn 30 ngày. Bấm *"Xác nhận ủy quyền"*. Giải thích: Quyền truy cập được tạo thành cam kết băm ngẫu nhiên neo trên Avalanche C-Chain, hoàn toàn không có PII.

---

## Phần 2 (1.5 phút) — Chuỗi Thời Gian & Xu Hướng (`/cases/[id]/timeline`)
- Mở một ca có sẵn đã được theo dõi 4 tuần.
- Cho thấy đồ thị biến thiên của **Chỉ số viêm đỏ (Erythema Index)** giảm dần từ 0.45 xuống 0.21.
- Chỉ vào huy hiệu **Có thể so sánh ảnh (`COMPARABLE`)**.
- Giải thích: Nếu hai lần chụp khác vùng da hoặc khác góc chụp vượt ngưỡng, hệ thống sẽ gắn nhãn `NOT_COMPARABLE` và từ chối vẽ xu hướng để bảo vệ tính an toàn lâm sàng.

---

## Phần 3 (1.5 phút) — Cổng Dành Cho Bác Sĩ Chuyên Khoa (`/doctor/inbox`)
- Nhấn đăng nhập nhanh tài khoản Bác sĩ `doctor@demo.test`.
- Mở ca bệnh nhân vừa gửi đến:
  - Cho thấy tính năng **Bảo mật ảnh gốc (Token 60 giây)**: Token đếm ngược và tự hủy.
  - Bác sĩ nhập điểm lâm sàng chính thống: **IGA = 2 (Nhẹ)** kèm lời dặn.
  - Nhấn Lưu: Điểm số lập tức được gắn huy hiệu **Clinician Verified (`clinician_entered`)**.
- Trở lại tài khoản bệnh nhân: Bấm **Thu hồi quyền truy cập (Revoke Consent)**.
- Quay lại màn hình bác sĩ: Bác sĩ bấm F5 -> Lập tức bị từ chối truy cập HTTP 403. Minh chứng sự tuân thủ off-chain tức thì.

---

## Kết Luận (30 giây)
- Tóm tắt 4 trụ cột: **Non-diagnostic An toàn**, **Mã hóa AES-256-GCM tại chỗ**, **GPS bảo tồn riêng tư**, và **Bằng chứng Blockchain Avalanche Zero-PII**.
- Sẵn sàng đón nhận câu hỏi từ Ban Giám Khảo.
