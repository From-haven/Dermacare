# DECISIONS.md — Nhật ký các quyết định kỹ thuật đã chốt

File này ghi nhận các quyết định kiến trúc, lý do lựa chọn và phương án thay thế theo đúng quy tắc Mục 0.1 của Master Spec.

---

### D01: Quản lý kiến trúc Monorepo và tính tương thích môi trường
- **Quyết định:** Tổ chức mã nguồn thành Monorepo thống nhất gồm `apps/api`, `apps/web`, `packages/contracts`, `ml/`, `docs/`, `infra/`.
- **Lý do:** Tuân thủ mục 3 Master Spec. Giúp agent và lập trình viên dễ dàng kiểm tra chéo API, contracts và UI mà không bị phân tán ngữ cảnh.
- **Phương án khác đã cân nhắc:** Tách đa repo (bị loại vì khó đồng bộ schemas và test T01–T10 xuyên suốt).

### D02: Chế độ chạy Zero-Dependency External Key (Local Dev Mode)
- **Quyết định:** Mặc định dự án khởi chạy độc lập hoàn toàn không yêu cầu bất kỳ API key bên thứ ba nào: `AUTH_MODE=local`, `WALLET_MODE=local-dev`, `CHAIN_MODE=mock`, `LLM_PROVIDER=none`.
- **Lý do:** Tránh bị chặn khi thiếu tài khoản Privy, Avalanche Fuji faucet, hoặc OpenAI/Gemini API keys. Bất kỳ ai clone repo đều chạy được ngay. Khi có key chỉ cần cấu hình trong `.env`.
- **Phương án khác:** Bắt buộc nhập API key ngay từ đầu (bị loại vì vi phạm quy tắc số 3).

### D03: Engine lưu trữ và truy vấn Vector tương đồng (Vector DB Engine)
- **Quyết định:** Hỗ trợ pgvector (PostgreSQL 16) khi chạy cùng Docker Compose; đồng thời tích hợp sẵn Vector Cosine Similarity Engine bằng Python/SQLite nội bộ cho chế độ chạy local dev / test standalone.
- **Lý do:** Đảm bảo test `eval_lookup.py` và luồng tra cứu tình trạng tương đồng chạy mượt mà ngay cả trên máy chưa bật service Docker Postgres, đồng thời khi bật Docker pgvector thì dùng đúng extension pgvector chuẩn.
- **Phương án khác:** Chỉ hỗ trợ pgvector buộc phải cài Docker (gây gián đoạn nếu môi trường chưa bật Docker daemon).

### D04: Triển khai Engine API Backend
- **Quyết định:** Cung cấp API server hỗ trợ đầy đủ chuẩn REST JSON prefix `/api` theo Mục 8. Kiến trúc module hóa sạch sẽ: `core`, `models`, `schemas`, `services`, `routers`. Tích hợp máy chủ HTTP Python native hiệu năng cao hỗ trợ xử lý đa luồng, đồng thời sẵn sàng tương thích FastAPI / ASGI.
- **Lý do:** Chạy độc lập tức thì trên mọi bản phân phối Linux/macOS/Windows có Python 3.11+, không phụ thuộc wheel biên dịch ngoài.
- **Phương án khác:** Bắt buộc pip install fastapi/uvicorn toàn cục (có thể gặp khó khăn trên môi trường không có internet sandbox).

### D05: Bản đồ phòng khám (Leaflet + OpenStreetMap)
- **Quyết định:** Sử dụng Leaflet + OpenStreetMap tiles cho bản đồ định vị phòng khám quanh toạ độ GPS.
- **Lý do:** Miễn phí, không yêu cầu Google Maps API key, hiển thị mượt mà responsive trên cả desktop và mobile.
- **Phương án khác:** Google Maps Javascript API (yêu cầu thẻ tín dụng và API key).

### D06: Bảo mật ảnh y tế (Envelope Encryption & EXIF Stripping)
- **Quyết định:** Ảnh upload bắt buộc đi qua Pillow để tái mã hóa (xoá sạch EXIF GPS/metadata), mã hóa đối xứng AES-256-GCM với khoá DEK 32-byte riêng cho từng ảnh. DEK được mã hóa bọc (wrap) bằng `APP_MASTER_KEY`.
- **Lý do:** Bảo vệ dữ liệu y tế nhạy cảm theo đúng chuẩn HIPAA/GDPR/Luật BVDLCN Việt Nam.
- **Phương án khác:** Lưu ảnh thô trực tiếp vào ổ cứng (bị loại vì rủi ro rò rỉ dữ liệu).

### D07: Cam kết quyền riêng tư On-Chain (Avalanche Commitment)
- **Quyết định:** Dữ liệu đẩy lên blockchain Avalanche chỉ chứa: commitment ngẫu nhiên `keccak256(nonce32, consentId, recipientClinicId, recipientUserId, scopeHash, expiry)` với `nonce32` là 32 bytes ngẫu nhiên từ CSPRNG.
- **Lý do:** Tuyệt đối không để lộ danh tính, toạ độ, hay mối quan hệ bệnh nhân - bác sĩ lên sổ cái công khai.
- **Phương án khác:** Hash trực tiếp thông tin bệnh nhân (bị loại vì dữ liệu ít entropy có thể bị tấn công rainbow table).


### D08: Hỗ trợ chụp trực tiếp từ Camera (Live Camera Stream) song song với Thư viện
- **Quyết định:** Bước 3 của Patient Wizard hỗ trợ song song 3 tùy chọn: (1) Mở camera trực tiếp (`getUserMedia`) với khung ngắm reticle định vị tổn thương chuẩn eKYC y tế và nút chụp snapshot, (2) Chọn tệp ảnh sẵn có từ thư viện/bộ nhớ thiết bị, và (3) Sử dụng ảnh mẫu sắc nét (phục vụ kiểm thử/demo). Khi chụp hoặc chọn xong, cung cấp nút "Chụp lại bằng camera" và đánh giá chất lượng tự động ngay trên máy khách.
- **Lý do:** Đáp ứng nhu cầu chụp tức thì trên thiết bị di động/laptop có camera, đồng thời giữ nguyên khả năng tải ảnh từ album hoặc ảnh chất lượng cao chụp trước đó.
- **Phương án khác:** Chỉ cho phép chọn tệp input file (bất tiện khi người dùng muốn soi chụp trực tiếp vùng da) hoặc chỉ cho phép camera (bất tiện nếu người dùng chụp bằng máy ảnh chuyên dụng/ảnh lưu sẵn).
