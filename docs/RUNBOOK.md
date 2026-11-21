# DermaCare Agent — Vận Hành, Sao Lưu & Xử Lý Sự Cố (Runbook)

## 1. Khởi Động & Giám Sát Dịch Vụ

### Chế độ Cục bộ (Local Development / Evaluation)
```bash
# 1. Khởi tạo môi trường và cơ sở dữ liệu
make bootstrap
make migrate

# 2. Nạp dữ liệu mẫu
make seed

# 3. Khởi chạy máy chủ tích hợp (Web UI + API)
make dev
# Mở trình duyệt tại: http://localhost:8000/
```

### Chế độ Production (Docker Compose)
```bash
docker compose -f infra/docker-compose.prod.yml up -d
```

Kiểm tra sức khỏe dịch vụ:
```bash
curl -f http://localhost:8000/health
```

---

## 2. Quy Trình Sao Lưu & Phục Hồi Dữ Liệu

### Sao lưu (Backup)
Tạo bản sao lưu nén chứa tệp cơ sở dữ liệu `derma.db` và toàn bộ tệp ảnh đã mã hóa `data/storage/`:
```bash
./apps/api/scripts/backup.sh
# Bản sao lưu được lưu tại: data/backups/derma_backup_<YYYYMMDD_HHMMSS>.tar.gz
```

### Phục hồi (Restore)
```bash
./apps/api/scripts/restore.sh data/backups/derma_backup_20261121_164733.tar.gz
```

---

## 3. Quy Trình Xoay Khóa Mật Mã (Key Rotation)

Khi cần xoay Master Key (`APP_MASTER_KEY`):
1. Tạo khóa mới 256-bit:
   ```bash
   python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
   ```
2. Lưu khóa mới vào biến môi trường `APP_MASTER_KEY_NEW`.
3. Chạy script xoay khóa để giải mã per-image DEK bằng khóa cũ và bọc lại (re-wrap) bằng khóa mới:
   ```bash
   python3 apps/api/scripts/rotate_keys.py
   ```
4. Cập nhật `.env` với `APP_MASTER_KEY = APP_MASTER_KEY_NEW` và xóa `APP_MASTER_KEY_NEW`.

---

## 4. Xử Lý Các Sự Cố Thường Gặp (Troubleshooting)

### Sự cố 1: Máy chủ không kết nối được mạng Avalanche Testnet
- **Hiện tượng:** Giao dịch neo bằng chứng bị timeout hoặc trả về lỗi RPC.
- **Biện pháp:**
  - Chuyển cấu hình `CHAIN_MODE=mock` trong `.env` để hệ thống tự động ghi nhận giao dịch vào bộ mô phỏng cục bộ mà không làm gián đoạn trải nghiệm của người dùng.
  - Sau khi mạng RPC phục hồi, chạy `python3 apps/api/scripts/retry_anchor.py` để đồng bộ lại các lô sự kiện đang chờ.

### Sự cố 2: Lỗi phân tích ảnh / Mô hình Vision không khả dụng
- **Hiện tượng:** Người dùng tải ảnh lên nhận được mã lỗi `MODEL_UNAVAILABLE`.
- **Biện pháp:**
  - Kiểm tra xem thư viện Pillow có bị thiếu trong môi trường không.
  - Hệ thống được thiết kế để không trả về kết quả giả định hoặc số liệu cũ khi mô hình gặp sự cố, đảm bảo an toàn y học tối đa.

### Sự cố 3: Người dùng khiếu nại không xem được ảnh
- **Hiện tượng:** Bác sĩ nhận được lỗi `IMAGE_TOKEN_EXPIRED`.
- **Giải thích:** Đây là tính năng bảo mật chủ động — token truy cập ảnh gốc chỉ có hiệu lực 60 giây. Bác sĩ chỉ cần tải lại trang chi tiết hồ sơ để nhận token mới.
