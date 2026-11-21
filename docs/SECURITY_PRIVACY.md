# DermaCare Agent — Chính Sách An Toàn & Bảo Mật Dữ Liệu Cá Nhân (Security & Privacy)

Tuân thủ nghiêm ngặt **Luật Bảo vệ Dữ liệu Cá nhân số 91/2025/QH15**, **Nghị định số 356/2025/NĐ-CP**, và tiêu chuẩn an toàn bảo mật y tế HIPAA/GDPR.

---

## 1. Ma Trận Phân Quyền Truy Cập (RBAC Matrix)

| Tài nguyên / Hành động | Patient (Chủ hồ sơ) | Clinician (Được cấp Consent) | Clinician (Ngoài phòng khám) | System Admin |
|------------------------|---------------------|------------------------------|------------------------------|--------------|
| Tạo ca theo dõi mới | Cho phép | Từ chối | Từ chối | Từ chối |
| Tải ảnh tổn thương | Cho phép | Từ chối | Từ chối | Từ chối |
| Xem chỉ số AI / Biểu đồ | Cho phép | Cho phép | 403 Forbidden | Từ chối (chỉ xem log) |
| Xem ảnh gốc (Token 60s) | Cho phép | Cho phép | 403 Forbidden | Từ chối |
| Nhập điểm lâm sàng (IGA/EASI) | Từ chối | Cho phép | Từ chối | Từ chối |
| Cấp / Thu hồi Consent | Cho phép | Từ chối | Từ chối | Từ chối |
| Xem nhật ký kiểm toán sạch | Từ chối | Từ chối | Từ chối | Cho phép |
| Phê duyệt Bác sĩ / Phòng khám | Từ chối | Từ chối | Từ chối | Cho phép |
| Xuất / Xóa vĩnh viễn hồ sơ | Cho phép | Từ chối | Từ chối | Chỉ hỗ trợ kỹ thuật |

---

## 2. Loại Bỏ Siêu Dữ Liệu Hình Ảnh (EXIF Stripping)
Khi người dùng tải ảnh từ điện thoại thông minh, tệp ảnh gốc thường chứa siêu dữ liệu nhạy cảm (vị trí GPS chính xác, số sê-ri máy ảnh, thời gian chụp).
- DermaCare Agent sử dụng thư viện xử lý ảnh để **tước bỏ 100% EXIF metadata** ngay lập tức trong bộ nhớ đệm trước khi lưu trữ.
- Đã được kiểm chứng tự động qua bộ test: Không còn bất kỳ trường EXIF định danh nào tồn tại trên tệp lưu trữ.

---

## 3. Mã Hóa Dữ Liệu Tại Chỗ (AES-256-GCM Envelope Encryption)
- Mỗi bức ảnh y tế được mã hóa bằng một khóa riêng biệt (Data Encryption Key - DEK) ngẫu nhiên 256-bit tạo bởi CSPRNG.
- Thuật toán `AES-256-GCM` cung cấp cả tính bảo mật (confidentiality) và tính toàn vẹn (integrity), chống can thiệp dữ liệu.
- DEK được bọc (wrap) bằng Master Key của ứng dụng (`APP_MASTER_KEY`).
- Khi người dùng xóa tài khoản, khóa bọc DEK bị hủy ngay lập tức, khiến dữ liệu ảnh trở thành các khối byte ngẫu nhiên không thể khôi phục (Crypto-shredding).

---

## 4. Xử Lý Tọa Độ GPS Bảo Tồn Riêng Tư (Privacy-Preserving GPS)
- Tọa độ GPS của người dùng chỉ được chuyển qua tham số tìm kiếm khoảng cách theo công thức Haversine trên RAM.
- **Tuyệt đối không lưu trữ tọa độ chi tiết vào Cơ sở dữ liệu hay Log hệ thống.**
- Trong nhật ký kiểm toán (Audit Logs), tọa độ chỉ được ghi lại ở mức làm tròn 2 chữ số thập phân (tương đương bán kính ~1.1 km), bảo vệ người dùng khỏi việc bị định vị nhà riêng.

---

## 5. Nguyên Tắc Không Lưu PII Trên Blockchain (Zero-PII on Chain)
- Các hợp đồng thông minh trên mạng Avalanche C-Chain (`ConsentRegistry.sol`, `TestSettlement.sol`) chỉ tiếp nhận:
  - Giá trị băm cam kết ngẫu nhiên (`Commitment Hash = sha256(salt || patient_id || clinic_id)`).
  - Giá trị băm gốc Merkle Audit Root (`bytes32 root`).
  - Mã tham chiếu hóa đơn thanh toán đối tác (`bytes32 invoiceRef`).
- Tuyệt đối không đưa tên tuổi, email, hình ảnh, triệu chứng hay chẩn đoán lên blockchain công khai.
