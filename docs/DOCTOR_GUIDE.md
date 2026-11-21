# DermaCare Agent — Hướng Dẫn Dành Cho Bác Sĩ Chuyên Khoa Da Liễu (Doctor Guide)

Tài liệu hướng dẫn quy trình lâm sàng, đánh giá hồ sơ bệnh nhân từ xa và bảo mật dữ liệu y tế dành cho Bác sĩ Da liễu.

---

## 1. Xác Thực Danh Tính & Điều Kiện Tiếp Nhận Hồ Sơ
- **Chứng chỉ hành nghề (CCHN):** Bác sĩ cần đăng ký tài khoản với mã số CCHN hợp lệ. Quản trị viên hệ thống sẽ kiểm tra và phê duyệt trạng thái `verified`.
- **Gói Verified Partner:** Để phòng khám của bác sĩ xuất hiện ưu tiên trên bản đồ và nhận hồ sơ gửi trực tiếp từ bệnh nhân, phòng khám phải có gói đối tác đang hoạt động (`partner_until` còn hiệu lực).

---

## 2. Hộp Thư Tiếp Nhận Hồ Sơ (`/doctor/inbox`)
- Danh sách các ca bệnh nhân đã chủ động cấp quyền (`Consent`) cho phòng khám của bạn.
- Hiển thị phạm vi chia sẻ (`full` hoặc `measurements_only`), thời hạn hiệu lực còn lại, và mốc quan sát gần nhất.

---

## 3. Xem Chi Tiết Ca Lâm Sàng (`/doctor/cases/[id]`)
- **Truy cập ảnh gốc an toàn (60-Second Temporary Image Token):**
  - Để ngăn ngừa rò rỉ dữ liệu y tế, hình ảnh tổn thương không được lưu trữ công khai.
  - Khi bác sĩ mở xem ảnh, hệ thống cấp một mã xác thực (Token) có thời hạn 60 giây. Quá 60 giây, token tự hủy và ảnh không thể truy cập lại nếu không yêu cầu mã mới.
- **Dữ liệu phân tích AI có Provenance:**
  - Độ nét ảnh (Sharpness Laplacian score).
  - Chỉ số viêm đỏ bán định lượng (Erythema index trên kênh LAB a*).
  - Tỷ lệ diện tích tổn thương (Lesion area percentage).
  - Đồ thị chuỗi thời gian nếu ảnh đạt tính tương thích (`COMPARABLE`).

---

## 4. Nhập Điểm Lâm Sàng Chuẩn Hóa & Nhận Xét Chuyên Khoa
Bác sĩ nhập điểm số đánh giá trực tiếp dựa trên các thang đo y học quốc tế:
- **IGA (Investigator's Global Assessment):** Thang điểm 0–4 (Clear to Severe) cho mụn trứng cá và viêm da cơ địa.
- **EASI (Eczema Area and Severity Index):** Điểm đánh giá mức độ lan rộng và độ nặng của chàm.
- **PASI (Psoriasis Area Severity Index):** Đánh giá tổn thương vảy nến mảng.

Mọi số điểm do bác sĩ nhập sẽ tự động gắn nhãn huy hiệu **Clinician Verified (`clinician_entered`)** trong báo cáo gửi về cho bệnh nhân.

---

## 5. Tư Vấn Trực Tuyến Qua Tin Nhắn Bảo Mật (`/consults/[consentId]`)
- Gửi tin nhắn hướng dẫn chăm sóc da, theo dõi diễn tiến hoặc đặt lịch hẹn khám trực tiếp.
- Khi bệnh nhân thu hồi Consent, kênh liên lạc và quyền truy cập hồ sơ sẽ bị vô hiệu hóa ngay tức khắc.
