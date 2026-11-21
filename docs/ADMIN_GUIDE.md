# DermaCare Agent — Hướng Dẫn Vận Hành Quản Trị Hệ Thống (Admin Guide)

Tài liệu dành cho Quản trị viên hệ thống (System Administrator) điều hành và giám sát nền tảng DermaCare Agent.

---

## 1. Phê Duyệt Bác Sĩ & Cơ Sở Y Tế (`/admin/verification`)
- **Duyệt Bác sĩ:**
  - Kiểm tra số Chứng chỉ Hành nghề (CCHN) và thông tin giấy phép do cơ quan y tế có thẩm quyền cấp.
  - Phê duyệt (`verified`) hoặc từ chối (`rejected`) tài khoản bác sĩ.
- **Duyệt Phòng khám:**
  - Xác thực giấy phép hoạt động khám chữa bệnh của cơ sở.
  - Kích hoạt trạng thái Verified Partner sau khi phòng khám thanh toán phí dịch vụ bằng token thử nghiệm Avalanche hoặc xác nhận hợp đồng đối tác.

---

## 2. Giám Sát Nhật Ký Kiểm Toán Không Chứa PII (`/admin/audit`)
- Hệ thống ghi lại toàn bộ sự kiện quan trọng (đăng ký, cấp quyền consent, thu hồi consent, vượt qua quality gate, v.v.).
- **Nguyên tắc Zero-PII Audit:**
  - Không lưu họ tên, địa chỉ email, số điện thoại trong nhật ký kiểm toán.
  - Tọa độ GPS của sự kiện được làm tròn tối đa 2 chữ số thập phân (bảo vệ quyền riêng tư vị trí).
  - Không lưu trữ dữ liệu thô của hình ảnh trong log.
  - Mỗi bản ghi mang một mã băm cam kết (Commitment Hash) và chuỗi liên kết Merkle audit log.

---

## 3. Quản Lý Neo Bằng Chứng Blockchain (Avalanche Anchoring)
- Quản trị viên có thể kích hoạt tiến trình gom lô (Batch Anchoring) các sự kiện kiểm toán:
  - Tính toán cây Merkle Tree từ danh sách các sự kiện chưa được neo.
  - Gửi giao dịch gọi hàm `anchorAudit(bytes32 root, uint256 batchId)` trên hợp đồng thông minh `ConsentRegistry.sol`.
  - Mọi bằng chứng trên chuỗi đều là giá trị băm mật mã học ngẫu nhiên, không thể đảo ngược ra dữ liệu cá nhân bệnh nhân.

---

## 4. Kiểm Tra Sức Khỏe Toàn Diện Hệ Thống (`/admin/system`)
- Trạng thái kết nối Cơ sở dữ liệu SQLite / PostgreSQL.
- Trạng thái dung lượng lưu trữ đối tượng mã hóa (Local Storage / MinIO).
- Trạng thái Blockchain Relayer (Avalanche Mock / Fuji Testnet).
- Tỷ lệ các ca bị từ chối bởi Quality Gate (mờ / tối / chói lóa).
