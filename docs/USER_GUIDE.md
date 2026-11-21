# DermaCare Agent — Hướng Dẫn Sử Dụng Dành Cho Bệnh Nhân (User Guide)

Chào mừng bạn đến với **DermaCare Agent**, ứng dụng hỗ trợ theo dõi tiến triển tổn thương da liễu cá nhân với cam kết bảo tồn quyền riêng tư và minh bạch y tế tối đa.

---

## 1. Lưu Ý Quan Trọng Trước Khi Dùng
> ⚠️ **TUYÊN BỐ GIỚI HẠN:** DermaCare Agent là công cụ hỗ trợ theo dõi tiến triển hình thái tổn thương da và đối sánh kiến thức tham khảo. Ứng dụng **không phải là bác sĩ**, **không đưa ra chẩn đoán y khoa**, và **không kê đơn thuốc**. Nếu bạn có các dấu hiệu nguy cấp (sốt cao, vết loét hoại tử, chảy máu không cầm được), hãy đến ngay cơ sở y tế gần nhất.

---

## 2. Quy Trình 6 Bước Tra Cứu & Đánh Giá Ban Đầu (`/start`)

1. **Bước 1 — Chọn vị trí da trên Sơ đồ Giải phẫu (Body Map):**
   - Chạm vào vùng da tương ứng trên sơ đồ (Mặt, Cổ, Ngực, Lưng, Cánh tay, v.v.).
2. **Bước 2 — Điền biểu hiện lâm sàng & Dấu hiệu cảnh báo đỏ:**
   - Chọn thời gian khởi phát tổn thương (dưới 1 tuần, vài tuần, vài tháng).
   - Đánh dấu cảm giác đi kèm (ngứa, đau rát, khô da, ửng đỏ).
   - Kiểm tra dấu hiệu cảnh báo đỏ (chảy máu, sốt, lan nhanh).
3. **Bước 3 — Chụp ảnh tổn thương (Quality Gate):**
   - Đặt camera cách tổn thương 15–20 cm.
   - Hệ thống tự động kiểm tra độ sắc nét, độ phơi sáng và chống lóa. Nếu ảnh bị mờ hoặc tối, hệ thống sẽ yêu cầu chụp lại để đảm bảo tính khách quan y học.
4. **Bước 4 — Xem danh sách tình trạng tương đồng tham khảo (`SimilarConditionsPanel`):**
   - Các tình trạng y khoa có biểu hiện tương tự được liệt kê theo thứ tự bảng chữ cái.
   - Không có tỷ lệ phần trăm xác suất hay xếp hạng nặng/nhẹ.
5. **Bước 5 — Tìm kiếm cơ sở Da liễu gần nhất:**
   - Hệ thống tính toán khoảng cách tức thì bằng GPS của trình duyệt (toạ độ không bao giờ được lưu trữ vào máy chủ).
   - Các phòng khám **Verified Partner** được đánh dấu nổi bật với khả năng tiếp nhận hồ sơ trực tuyến.
6. **Bước 6 — Cấp quyền chia sẻ hồ sơ (Consents):**
   - Lựa chọn phạm vi chia sẻ (Toàn bộ hồ sơ hoặc Chỉ chia sẻ số đo) và thời hạn hiệu lực (7, 14, hoặc 30 ngày).

---

## 3. Theo Dõi Tiến Triển Theo Thời Gian (`/cases/[id]/timeline`)
- Mỗi lần chụp ảnh mới cùng vị trí, hệ thống sẽ đối sánh và đánh giá tính tương thích (`COMPARABLE`).
- Khi tích lũy từ 3 lần theo dõi trở lên với ảnh đạt chuẩn, đồ thị xu hướng chỉ số viêm đỏ và diện tích tổn thương sẽ được hiển thị kèm huy hiệu **AI Measured**.

---

## 4. Quản Lý Quyền Riêng Tư & Dữ Liệu Cá Nhân
- **Thu hồi quyền truy cập:** Bạn có thể thu hồi sự ủy quyền với phòng khám bất kỳ lúc nào tại màn hình `/sharing`. Sau khi thu hồi, bác sĩ sẽ lập tức bị chặn truy cập vào hình ảnh và hồ sơ của bạn.
- **Tải về dữ liệu:** Truy cập `/settings` để xuất toàn bộ dữ liệu cá nhân dạng JSON (tuân thủ Luật Bảo vệ Dữ liệu Cá nhân 91/2025/QH15).
- **Xóa vĩnh viễn tài khoản:** Nhấn nút xóa tài khoản tại `/settings` để xóa sạch toàn bộ hồ sơ và ảnh đã mã hóa.
