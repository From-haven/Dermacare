# DermaCare Agent — Đề Cương Thử Nghiệm Lâm Sàng Thuần Tập Dọc (Pilot Protocol)

Đề cương đánh giá hiệu năng theo dõi dọc (Longitudinal Cohort Study) và tính an toàn của hệ thống DermaCare Agent trên quần thể thực tế.

---

## 1. Mục Tiêu Nghiên Cứu
1. **Mục tiêu chính:** Đánh giá tính nhất quán và độ tương quan giữa chỉ số viêm đỏ bán định lượng do AI trích xuất (`ai_measured`) với thang điểm đánh giá lâm sàng IGA do bác sĩ da liễu cho điểm (`clinician_entered`) qua chuỗi thời gian 8 tuần.
2. **Mục tiêu phụ:** Đánh giá tỷ lệ người dùng tuân thủ chụp ảnh theo đúng quy chuẩn Quality Gate và mức độ hài lòng về tính năng bảo vệ quyền riêng tư.

---

## 2. Tiêu Chí Chọn Mẫu & Loại Trừ
- **Tiêu chuẩn lựa chọn (Inclusion Criteria):**
  - Người tham gia từ 18 tuổi trở lên.
  - Có tổn thương da dạng viêm (mụn trứng cá viêm hoặc viêm da cơ địa nhẹ đến trung bình) tại các vùng giải phẫu: Mặt, Cánh tay, Lưng.
  - Tự nguyện ký bản đồng thuận tham gia nghiên cứu (Informed Consent).
- **Tiêu chuẩn loại trừ (Exclusion Criteria):**
  - Tổn thương có dấu hiệu nghi ngờ ác tính (nốt ruồi thay đổi màu sắc, bờ không đều).
  - Tổn thương nhiễm trùng cấp tính có mủ lan rộng hoặc hoại tử.
  - Không có thiết bị chụp ảnh độ phân giải tối thiểu 1024x768.

---

## 3. Quy Trình Thu Thập Dữ Liệu Dọc (8 Tuần)
- **Mốc T0 (Khởi đầu):** Bác sĩ khám trực tiếp, xác định thể bệnh và chấm điểm IGA ban đầu. Bệnh nhân chụp ảnh cơ sở (baseline) qua ứng dụng.
- **Mốc T1 đến T7 (Hàng tuần):** Bệnh nhân nhận thông báo nhắc nhở tự chụp ảnh tại nhà theo đúng góc chụp và điều kiện ánh sáng chuẩn. Quality Gate đánh giá độ nét và phơi sáng.
- **Mốc T8 (Kết thúc):** Bác sĩ đánh giá lại toàn bộ chuỗi ảnh và chấm điểm kết thúc.

---

## 4. Đạo Đức Nghiên Cứu & Bảo Vệ Quyền Riêng Tư
- Đề cương phải được Hội đồng Đạo đức trong Nghiên cứu Y sinh học phê duyệt trước khi tuyển bệnh nhân thật đầu tiên.
- Toàn bộ ảnh được lưu trữ dưới dạng mã hóa per-image DEK. Không có thông tin định danh (PII) nào được chia sẻ ra ngoài phạm vi nhóm nghiên cứu.
- Người tham gia có quyền rút khỏi nghiên cứu bất kỳ lúc nào; toàn bộ dữ liệu sẽ được xóa vĩnh viễn (Crypto-shredding) ngay khi nhận được yêu cầu.
