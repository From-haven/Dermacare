# DermaCare Agent — Thông Tin Phát Hành (Release Notes v1.0.0)

**Phiên bản:** `1.0.0`  
**Ngày phát hành:** 21/11/2026  
**Trạng thái:** Production Ready (với nhãn Synthetic/Demo y tế chuẩn hóa)

---

## 1. Tính Năng Nổi Bật

### 🔬 Thị Giác Máy Tính & Quality Gate Y Tế
- **Cổng kiểm tra chất lượng ảnh tự động (Quality Gate):** Đo lường phương sai Laplacian (độ sắc nét), độ phơi sáng trung bình (luminance), tỷ lệ chói lóa (glare ratio), và độ phân giải hình ảnh. Tự động trả về khuyến nghị chụp lại cụ thể nếu ảnh không đạt tiêu chuẩn.
- **Trích xuất số đo bán định lượng có Provenance:** Tính toán chỉ số viêm đỏ Erythema Index trên kênh LAB a* với ngưỡng thích ứng Otsu, tỷ lệ diện tích tổn thương (% vùng quan sát).
- **Bộ đánh giá tính tương thích ảnh (Comparability Evaluator):** Phân loại `COMPARABLE`, `PARTIAL`, hoặc `NOT_COMPARABLE`. Ngừng tính toán xu hướng chênh lệch nếu góc chụp hoặc vùng giải phẫu không tương thích.

### 📚 Tra Cứu Tình Trạng Tương Đồng Minh Bạch
- **Cơ sở kiến thức 20 tình trạng da liễu chuẩn y văn (Phụ lục B):** Nạp đầy đủ véc-tơ đặc trưng 64 chiều (`fv-1`), tìm kiếm cosine độ tương đồng.
- **Tuân thủ quy chuẩn y học nghiêm ngặt:** Sắp xếp theo thứ tự bảng chữ cái; không hiển thị tỷ lệ %, không chấm điểm độ nặng, không đưa ra phán quyết khẳng định; luôn đi kèm tuyên bố giới hạn cố định.

### 📍 Đối Sánh Phòng Khám & Gói Verified Partner
- **Tìm kiếm GPS bảo tồn riêng tư:** Tính toán khoảng cách theo công thức Haversine trên bộ nhớ tạm; tuyệt đối không lưu tọa độ chi tiết vào DB hay log.
- **Danh bạ 6 cơ sở da liễu thực tế tại TP.HCM (Phụ lục D):** Cơ sở thật không bị gắn nhãn thương mại giả mạo. Cơ sở đối tác được ưu tiên hiển thị trước và hỗ trợ gửi hồ sơ trực tuyến.

### ⛓️ Neo Bằng Chứng Kiểm Toán Trên Avalanche (Zero-PII)
- **Hợp đồng thông minh ConsentRegistry.sol:** Cấp và thu hồi quyền truy cập hồ sơ qua cam kết ngẫu nhiên (CSPRNG salt).
- **Cây Merkle Audit Root:** Gom lô các sự kiện kiểm toán hệ thống và neo gốc Merkle lên mạng Avalanche C-Chain mà không lộ bất kỳ thông tin cá nhân (PII) nào.
- **Thanh toán gói đối tác qua TestSettlement.sol:** Cho phép phòng khám mua và gia hạn gói Verified Partner bằng token thử nghiệm DERMA Test Token.

---

## 2. Các Thay Đổi & Sửa Lỗi Trong Phiên Bản
- Tối ưu hóa thuật toán tính Laplacian bằng toán tử chập C-level thuần trong Pillow, loại bỏ phụ thuộc vào thư viện bên ngoài nặng.
- Ngăn chặn triệt để tấn công Prompt Injection vào AI Agent bằng LLM Guard đa lớp (Fact-checking, Sanitizer, Forbidden terms filter).
- Triển khai toàn diện giao diện Web responsive, hỗ trợ song ngữ Tiếng Việt / Tiếng Anh với thiết kế chuẩn y khoa.
