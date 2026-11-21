# DermaCare Agent — Hướng Dẫn Triển Khai Production (Deployment Guide)

Tài liệu hướng dẫn triển khai hệ thống DermaCare Agent trên môi trường thực tế (Docker, Cloud VPS, Vercel, Render/Fly.io).

---

## 1. Triển Khai Bằng Docker Compose (Khuyến nghị)

### Bước 1: Chuẩn bị tệp cấu hình môi trường `.env`
Tạo tệp `.env` trên máy chủ từ bản mẫu:
```bash
cp .env.example .env
python3 apps/api/scripts/gen_keys.py --env
```
Thiết lập các biến quan trọng:
```ini
APP_ENV=prod
AUTH_MODE=local
WALLET_MODE=local-dev
CHAIN_MODE=mock
DATABASE_URL=postgresql://derma_user:derma_pass@db:5432/derma_db
APP_MASTER_KEY=<32_bytes_base64_key>
JWT_SECRET=<hex_secret>
```

### Bước 2: Khởi chạy các container
```bash
docker compose -f infra/docker-compose.prod.yml up -d --build
```

Container bao gồm:
1. `api`: Máy chủ FastAPI / Python HTTP phục vụ API và Static Web.
2. `worker`: Tiến trình nền xử lý các tác vụ kiểm toán Merkle và định thời.
3. `db`: PostgreSQL 16 tích hợp tiện ích mở rộng vector `pgvector`.
4. `minio`: Lưu trữ đối tượng S3-compatible riêng tư cho ảnh mã hóa.
5. `redis`: Bộ đệm và hàng đợi tác vụ.

### Bước 3: Khởi tạo schema và nạp dữ liệu
```bash
docker compose -f infra/docker-compose.prod.yml exec api python3 apps/api/scripts/seed.py
```

---

## 2. Triển Khai Tách Biệt (Hybrid Cloud)

- **Frontend (Web App):** Triển khai lên **Vercel** từ thư mục `apps/web/`.
  - Cấu hình biến môi trường: `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`
- **Backend API:** Triển khai lên **Render**, **Railway**, hoặc **Fly.io** từ `apps/api/`.
  - Cổng lắng nghe: `PORT=8000`
  - Đính kèm Managed PostgreSQL (hỗ trợ `pgvector`).
- **Lưu trữ ảnh mã hóa:** Sử dụng **Cloudflare R2** hoặc **AWS S3** với bucket riêng tư (Private Bucket), không bật Public Read.

---

## 3. Cấu Hình Tên Miền & Chứng Chỉ HTTPS
Sử dụng Nginx hoặc Caddy làm Reverse Proxy chuyển tiếp:
```nginx
server {
    server_name dermacare.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Cài đặt chứng chỉ SSL tự động qua Let's Encrypt:
```bash
sudo certbot --nginx -d dermacare.yourdomain.com
```
