# DermaCare Agent

> **Tra cứu biểu hiện da • Theo dõi dài hạn • Kết nối phòng khám da liễu theo GPS**

DermaCare Agent là ứng dụng web y tế toàn diện được xây dựng theo kiến trúc và đặc tả chuẩn trong [docs/spec/MASTER_SPEC.md](file:///run/media/raphael/Partition_D/hackathon/docs/spec/MASTER_SPEC.md).

---

## 1. Giới hạn y tế & Miễn trừ trách nhiệm (Medical Disclaimer)

> [!WARNING]
> **DermaCare Agent là công cụ tham khảo và theo dõi, KHÔNG PHẢI CHẨN ĐOÁN Y KHOA.**
> - Hệ thống **không chẩn đoán, không kê đơn, không khuyên ngưng thuốc**, không khẳng định lành/ác tính.
> - Danh sách các tình trạng da tương đồng **không hiển thị phần trăm (%), không xếp hạng mức độ bệnh, không đánh giá mức độ khẩn cấp suy từ ảnh**.
> - Danh sách tra cứu tương đồng được sinh từ Cơ sở Kiến thức (Vector DB pgvector 64 chiều) đã duyệt, tuyệt đối không để LLM tự chẩn đoán bệnh.
> - Bất kỳ dấu hiệu khẩn cấp nào (sốt cao kèm phát ban lan nhanh, sưng mặt/môi/khó thở, phồng rộp quanh mắt/miệng) sẽ lập tức kích hoạt **Safety Router** để dừng luồng và hướng dẫn gọi **Cấp cứu 115**.
> - Gói **Verified Partner** là gói dịch vụ kỹ thuật kết nối của phòng khám đối tác, **không phải chứng nhận chất lượng y khoa**.

---

## 2. Tính năng chính (6 bước User Flow)

1. **Khai báo triệu chứng trực quan**: Chọn vùng cơ thể trên Body Map SVG tương tác, trả lời form triệu chứng trực quan render động từ YAML (`intake_general.yaml`).
2. **Chụp ảnh chuẩn khung eKYC**: Camera hướng dẫn theo từng bộ phận với client-side canvas pre-check và server-side **Quality Gate** (độ nét Laplacian, phơi sáng, loá, độ phân giải, tỉ lệ khung).
3. **Phân tích hình ảnh & Tra cứu Vector DB**: Trích xuất chỉ số lặp lại (`affected_area_ratio` heuristic LAB-Otsu), kết hợp form triệu chứng thành vector đặc trưng 64 chiều (`fv-1`) và truy vấn Cosine Similarity trên pgvector để trả về danh sách tình trạng tương đồng.
4. **Tìm phòng khám gần nhất (GPS)**: Xác định khoảng cách haversine từ toạ độ người dùng đến các cơ sở y tế. Phòng khám Verified Partner được hiển thị ưu tiên với nút "Gửi hồ sơ & Tư vấn ngay". Toạ độ GPS người dùng **không lưu vào database** và log chỉ làm tròn 2 chữ số thập phân.
5. **Chia sẻ hồ sơ an toàn & Tư vấn**: Người dùng chọn phạm vi chia sẻ (scope) và thời hạn. Bằng chứng cấp quyền được bảo chứng trên Avalanche C-Chain qua commitment ẩn danh (Zero PII). Bác sĩ phòng khám xem ảnh gốc với token 60s, nhập review chuyên môn và nhắn tin tư vấn trực tiếp.
6. **Theo dõi tiến triển (Timeline) & Báo cáo PDF**: Thuật toán so sánh (Comparator) kiểm tra tính tương thích giữa các lần chụp; hiển thị biểu đồ chỉ số riêng biệt với huy hiệu **Provenance** rõ ràng (`ai_measured`, `user_reported`, `clinician_entered`, `synthetic`). Xuất báo cáo PDF chuyên nghiệp cho bác sĩ.

---

## 3. Khởi động nhanh (Quickstart)

```bash
# 1. Khởi tạo cấu hình và sinh khóa mật mã
make bootstrap

# 2. Khởi chạy hệ thống (API Server + Web UI tại http://localhost:3000)
make dev

# 3. Chạy toàn bộ test tự động (T01 – T10)
make test
```

### Tài khoản đăng nhập demo (chỉ dùng cho môi trường phát triển):
- **Bệnh nhân:** `patient@demo.test` / `Password123!`
- **Bác sĩ đối tác:** `doctor@demo.test` / `Password123!`
- **Quản trị viên:** `admin@demo.test` / `Password123!`

---

## 4. Cấu trúc mã nguồn

```
dermacare/
├── apps/
│   ├── api/          # Backend API (REST /api, Core Crypto, RBAC, Services, Routers)
│   └── web/          # Frontend Web (UI Wizard, Body Map, Leaflet GPS Map, Dashboards)
├── ml/               # Vision baseline (Quality gate, LAB Otsu segment, Vector embedder)
├── packages/contracts/# Smart Contracts Solidity ^0.8.24 (ConsentRegistry, Settlement)
├── docs/             # Tài liệu kiến trúc, hướng dẫn sử dụng, báo cáo bảo mật
└── infra/            # Docker Compose (PostgreSQL pgvector, Redis, MinIO)
```

Xem chi tiết tại [docs/ARCHITECTURE.md](file:///run/media/raphael/Partition_D/hackathon/docs/ARCHITECTURE.md).


---

## 5. Tài Liệu Kỹ Thuật & Hướng Dẫn Sử Dụng (Documentation Index)

Toàn bộ tài liệu chính thức được lưu trữ trong thư mục `docs/`:

- [docs/ARCHITECTURE.md](file:///run/media/raphael/Partition_D/hackathon/docs/ARCHITECTURE.md) — Kiến trúc hệ thống, sơ đồ tuần tự và 4 tầng Provenance.
- [docs/USER_GUIDE.md](file:///run/media/raphael/Partition_D/hackathon/docs/USER_GUIDE.md) — Hướng dẫn quy trình 6 bước dành cho Bệnh nhân.
- [docs/DOCTOR_GUIDE.md](file:///run/media/raphael/Partition_D/hackathon/docs/DOCTOR_GUIDE.md) — Hướng dẫn duyệt hồ sơ, xem ảnh bảo mật 60s và cho điểm IGA/EASI cho Bác sĩ.
- [docs/ADMIN_GUIDE.md](file:///run/media/raphael/Partition_D/hackathon/docs/ADMIN_GUIDE.md) — Hướng dẫn quản trị hệ thống, phê duyệt bác sĩ và nhật ký kiểm toán.
- [docs/RUNBOOK.md](file:///run/media/raphael/Partition_D/hackathon/docs/RUNBOOK.md) — Sổ tay vận hành, sao lưu, phục hồi dữ liệu và xử lý sự cố.
- [docs/SECURITY_PRIVACY.md](file:///run/media/raphael/Partition_D/hackathon/docs/SECURITY_PRIVACY.md) — Ma trận RBAC, tước bỏ EXIF, mã hóa AES-256-GCM và Zero PII on-chain.
- [docs/TEST_REPORT.md](file:///run/media/raphael/Partition_D/hackathon/docs/TEST_REPORT.md) — Báo cáo kiểm thử tự động, ánh xạ đầy đủ T01–T10.
- [docs/BLOCKCHAIN_EVIDENCE.md](file:///run/media/raphael/Partition_D/hackathon/docs/BLOCKCHAIN_EVIDENCE.md) — Hợp đồng thông minh Avalanche, ABI và bằng chứng cam kết mật mã.
- [docs/DEPLOY.md](file:///run/media/raphael/Partition_D/hackathon/docs/DEPLOY.md) — Hướng dẫn triển khai Production qua Docker, Vercel và Render.
- [docs/DEMO_SCRIPT.md](file:///run/media/raphael/Partition_D/hackathon/docs/DEMO_SCRIPT.md) — Kịch bản trình diễn trực tiếp (Live Demo) từng bước.
- [docs/PILOT_PROTOCOL.md](file:///run/media/raphael/Partition_D/hackathon/docs/PILOT_PROTOCOL.md) — Đề cương thử nghiệm lâm sàng thuần tập dọc (Pilot Study).
- [docs/RELEASE_CHECKLIST.md](file:///run/media/raphael/Partition_D/hackathon/docs/RELEASE_CHECKLIST.md) — Bảng kiểm nghiệm thu phát hành phiên bản 1.0.0.
- [docs/OPENAPI.json](file:///run/media/raphael/Partition_D/hackathon/docs/OPENAPI.json) — Đặc tả kỹ thuật OpenAPI 3.1.0 chuẩn hóa cho REST API.
- [ml/MODEL_CARD.md](file:///run/media/raphael/Partition_D/hackathon/ml/MODEL_CARD.md) — Thẻ mô hình thị giác máy tính và cơ chế từ chối (Abstention).
- [ml/DATASET_REGISTER.md](file:///run/media/raphael/Partition_D/hackathon/ml/DATASET_REGISTER.md) — Sổ đăng ký bộ dữ liệu y tế và quy chuẩn bản quyền.

---

## 6. Hướng Dẫn Dành Cho Windows & WSL2 (Foundry)

Nếu bạn chạy trên hệ điều hành Windows:
1. Mở terminal **WSL2** (Ubuntu 22.04 / 24.04).
2. Di chuyển vào thư mục dự án và cài đặt Foundry:
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```
3. Chạy kiểm thử hợp đồng thông minh trong WSL2:
   ```bash
   cd packages/contracts && forge test -v
   ```
4. Trên môi trường không cài sẵn Foundry, DermaCare Agent tự động kích hoạt bộ giả lập EVM tích hợp sẵn trong Python (`tests/test_contracts.py`) giúp mọi bài test hợp đồng thông minh vẫn pass 100% độc lập.
