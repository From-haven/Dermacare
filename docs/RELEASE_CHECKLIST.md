# DermaCare Agent — Danh Sách Kiểm Tra Phát Hành (Release Checklist)

Bảng kiểm nghiệm thu trước khi triển khai hệ thống DermaCare Agent phiên bản 1.0.0.

---

## 1. Kiểm Tra An Toàn Y Học & Giao Diện (Medical Safety & UI)
- [x] **Banner cố định:** Tuyên bố giới hạn *"Công cụ tham khảo & theo dõi, không phải chẩn đoán"* hiển thị ở đầu mọi màn hình web.
- [x] **Bảng tình trạng tương đồng (`SimilarConditionsPanel`):**
  - [x] Sắp xếp nghiêm ngặt theo thứ tự bảng chữ cái.
  - [x] Tuyệt đối không hiển thị tỷ lệ phần trăm xác suất (`%`).
  - [x] Không chấm điểm hay xếp hạng độ nặng nhẹ của bệnh.
  - [x] Kèm theo cảnh báo an toàn bắt buộc và nguồn y văn trích dẫn.
- [x] **Rà soát chuỗi ký tự cấm (String Scan Test):** Không chứa bất kỳ cụm từ chẩn đoán y khoa khẳng định nào (`"bạn bị mắc"`, `"khỏi bệnh"`, `"nặng hơn"`, `"nguy hiểm"`).
- [x] **Provenance Badges:** 100% các số liệu hiển thị có huy hiệu nguồn gốc (`ai_measured`, `user_reported`, `clinician_entered`, `synthetic`).
- [x] **Đánh dấu dữ liệu mẫu:** Nhãn `DEMO / SYNTHETIC` hiển thị rõ ràng trên mọi màn hình sử dụng dữ liệu giả lập.

---

## 2. Kiểm Tra An Toàn Thị Giác Máy Tính (Vision & ML Gate)
- [x] **Cổng kiểm tra chất lượng ảnh (Quality Gate):** Ảnh mờ (Laplacian < 100) hoặc tối (Luminance < 50) bị từ chối với nhãn `RETAKE`.
- [x] **Đánh giá tính tương thích (Comparability Gate):** Ảnh khác vùng giải phẫu bị gắn cờ `NOT_COMPARABLE` và ngừng tính toán delta xu hướng.
- [x] **Nguyên tắc từ chối (Abstention):** Các ca ngoài danh mục hoặc mô hình gián đoạn trả về `ABSTAIN` / `MODEL_UNAVAILABLE`, không bịa kết quả.

---

## 3. Kiểm Tra Bảo Mật Dữ Liệu & Quyền Riêng Tư (Security & Privacy)
- [x] **Tước bỏ EXIF:** 100% siêu dữ liệu EXIF (GPS, thiết bị, camera serial) bị xóa trước khi lưu trữ.
- [x] **Mã hóa AES-256-GCM:** Mỗi bức ảnh có một khóa DEK 256-bit riêng biệt được bọc bởi Master Key.
- [x] **Truy cập ảnh qua Token ngắn hạn:** Bác sĩ chỉ truy cập ảnh gốc qua JWT token có thời hạn 60 giây.
- [x] **Tọa độ GPS bảo tồn riêng tư:** Tọa độ người dùng chỉ tính toán khoảng cách tức thời trên RAM, không bao giờ lưu vào Database; tọa độ trong audit log được làm tròn 2 chữ số thập phân (~1.1 km).
- [x] **Ma trận RBAC & Vòng đời Consent:** Bác sĩ không có Consent hoặc có Consent đã bị thu hồi bị trả về mã lỗi HTTP 403 ngay lập tức.
- [x] **Quyền dữ liệu cá nhân (Luật 91/2025/QH15 & GDPR):** Người dùng có quyền xuất tệp JSON hoặc xóa vĩnh viễn tài khoản.

---

## 4. Kiểm Tra Bằng Chứng Blockchain (Avalanche C-Chain)
- [x] **Zero-PII On-Chain:** Kiểm tra tự động 100% payload gửi chuỗi: không chứa email, họ tên, số điện thoại, ảnh, hoặc tọa độ.
- [x] **Cam kết ngẫu nhiên (Commitment):** Cấp và thu hồi quyền chia sẻ thông qua giá trị băm CSPRNG salt.
- [x] **Hợp đồng thông minh:** `ConsentRegistry.sol`, `DermaTestToken.sol`, `TestSettlement.sol` được kiểm thử toàn diện bằng Foundry và bộ test Python.
- [x] **Xử lý lỗi giao dịch:** Khi giao dịch thất bại, hệ thống ghi nhận trạng thái `FAILED`, không gian lận kích hoạt dịch vụ đối tác.

---

## 5. Kiểm Thử Tự Động & Tài Liệu Nghiệm Thu
- [x] Bộ test tự động `tests/test_*.py` đạt **65/65 PASS**.
- [x] Ánh xạ đầy đủ bộ test bắt buộc **T01 đến T10**.
- [x] Đầy đủ 100% tài liệu theo yêu cầu Mục 20 của MASTER_SPEC trong thư mục `docs/`.
- [x] Script nạp dữ liệu mẫu `make seed` hoạt động hoàn hảo.
