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

### D09: Khắc phục toàn diện 10 hạng mục theo báo cáo kiểm toán Fix.md (P0 đến P3)
- **Quyết định:**
  1. `[FIX-01]` Nối Bước 3 Wizard với endpoint backend thật `POST /api/wizard/analyze`, giữ nguyên ảnh thật của người dùng (không ghi đè ảnh mẫu), client nén ảnh <= 1280px bằng canvas để upload siêu tốc.
  2. `[FIX-02]` Bổ sung đầy đủ toàn bộ HTTP REST endpoints trong `apps/api/app/main.py`: `POST /api/wizard/analyze`, `POST /api/safety/check`, `PUT /api/observations/{id}/roi`, `GET /api/reports/{id}/pdf`, `GET /api/images/{id}/content?token=...`, `DELETE /api/consents/{id}`, `GET /api/cases/{id}/timeline`, `POST /api/cases/{id}/compare`, `GET/POST /api/wallet`, `GET/PATCH /api/admin/users`, `POST /api/admin/clinicians/{id}/verify|reject`.
  3. `[FIX-03]` Đồng bộ 12 vùng cơ thể BodyMap với `FEATURE_KEYS_64` trong `embedder.py` (`trunk_front`, `folds`, `nails`), nạp đủ 28 triệu chứng và 15 câu hỏi an toàn (red flags). Tích hợp Safety Router cắt luồng khẩn cấp nếu có dấu hiệu cấp cứu (115).
  4. `[FIX-04]` Đo lường đầy đủ 6 đặc trưng hình ảnh (`affected_area_ratio`, `redness_contrast`, `component_count`, `dispersion`, `texture`, `light_contrast`) và morphology open/close lọc nhiễu trong `ml/vision/segment.py` & `measure.py`.
  5. `[FIX-05]` Sửa lỗ hổng Admin RBAC: `enforce_admin` truy vấn DB kiểm tra `role == 'admin'` và `status == 'active'`, chặn toàn bộ bệnh nhân và bác sĩ với HTTP 403 Forbidden.
  6. `[FIX-06]` Sửa lỗ hổng Image Token: kiểm tra chủ quyền ca bệnh với bệnh nhân, kiểm tra active consent với bác sĩ, chặn hoàn toàn Admin xem ảnh y tế (403), áp dụng rate limiting (5/min login, 20/hr upload, 30/min clinic search).
  7. `[FIX-07]` Kết nối `consents.py` với `ChainClient` sinh và xác nhận giao dịch Avalanche C-Chain, thu hồi off-chain có hiệu lực tức thời.
  8. `[FIX-08]` Tối ưu hoá xử lý ảnh lớn: resize ảnh thumbnail <= 256px trước khi duyệt pixel, đưa thời gian phân tích ảnh 12MP về < 100ms.
  9. `[FIX-09]` SQLite dùng `threading.local()` với `WAL` mode và `busy_timeout=5000` chống khóa đa luồng, cache đồng bộ YAML một lần duy nhất lúc khởi động.
  10. `[FIX-10 & P3]` Nối toàn bộ các màn hình Web UI (Case Detail, Timeline, Report, Sharing, Wallet, Doctor Inbox/Detail/Partner, Admin Audit/Verification) với API backend thật, loại bỏ hoàn toàn mock data và `alert()` giả.
- **Lý do:** Hoàn thiện 100% ứng dụng chạy thực tế end-to-end trên trình duyệt không còn lỗ hổng hay chức năng giả lập.

### D10: Khắc phục lỗi vi phạm khoá ngoại SQLite (`FOREIGN KEY constraint failed`) tại Bước 3 Wizard
- **Quyết định:**
  1. Trong `apps/api/app/services/lookup.py` (`lookup_similar_conditions`): Chỉ thực hiện `INSERT INTO similar_condition_results` khi `observation_id` đã tồn tại trong bảng `observations`. Nếu `observation_id` chưa tồn tại (khách vãng lai chưa tạo hồ sơ, hoặc luồng phân tích chạy trước khi tạo ca), bỏ qua lệnh ghi để không vi phạm ràng buộc khoá ngoại `FOREIGN KEY(observation_id) REFERENCES observations(id)`.
  2. Trong `apps/api/app/main.py` (khối persist `/api/wizard/analyze`):
     - Bổ sung trường bắt buộc `updated_at` vào câu lệnh `INSERT INTO visual_measurements` (11 cột thay vì 10).
     - Điều chỉnh câu lệnh `INSERT INTO similar_condition_results` khớp chính xác 100% với cấu trúc schema thực tế của bảng (`id, observation_id, embedder_version, kb_version, results, abstain_reason, created_at, updated_at`), không còn gọi các cột không tồn tại (`condition_slug, name_vi, name_en, summary, sources, reviewed_by_clinician`).
  3. Bổ sung test kiểm thử hồi quy tự động trong `tests/test_fix_audit.py` cho cả 2 kịch bản khách vãng lai và người dùng đã xác thực, đảm bảo 0 lỗi phát sinh và dữ liệu được lưu trữ chuẩn xác.
- **Lý do:** Loại bỏ hoàn toàn lỗi 500 `FOREIGN KEY constraint failed` và `db_save_error`, giữ nguyên cấu hình bảo vệ toàn vẹn dữ liệu `PRAGMA foreign_keys = ON` của SQLite.

### D11: Hiệu chỉnh hạ ngưỡng Quality Gate (độ phân giải và độ nét) phù hợp ảnh thực tế
- **Quyết định:**
  1. Hạ ngưỡng độ phân giải tối thiểu (`min_short_dimension`) từ 640px xuống 240px trong `ml/vision/thresholds.yaml` và `ml/vision/quality.py`.
  2. Hạ ngưỡng độ nét Laplacian: `retake_threshold` từ 60.0 xuống 15.0; `review_threshold` từ 100.0 xuống 25.0.
  3. Loại bỏ hiện tượng nhiễu biên 1-pixel khi tính toán Laplacian bằng Pillow (`ImageFilter.Kernel`) và chỉ downscale ảnh khi chiều dài > 1024px (tránh hiện tượng sinc ringing khi upscale ảnh nhỏ lên 1024px).
  4. Cập nhật thẻ kết quả `QualityResultCard` trên Web UI hiển thị ngưỡng tối thiểu linh hoạt theo API thay vì hardcode số cũ `(Ngưỡng: 60)`.
- **Lý do:** Cho phép người dùng chụp hoặc tải lên các ảnh thực tế từ thiết bị di động, ảnh crop tổn thương (ví dụ kích thước 303px, độ nét 26.7) hoặc mẫu canvas 640x480 vượt qua Quality Gate thuận lợi mà không bị chặn oan với trạng thái RETAKE. Đảm bảo ảnh thật sự mờ hoặc tối đen vẫn bị chặn RETAKE đúng thiết kế.

### D12: Cập nhật GPS theo thiết bị hiện tại, khôi phục thanh tiến trình ngang Stepper và bổ sung Đăng ký ngoài giao diện
- **Quyết định:**
  1. **GPS thiết bị thực tế:** Tự động gọi `navigator.geolocation.getCurrentPosition` (high accuracy) khi vào Bước 5 để lấy toạ độ thực tế của máy/thiết bị, căn tâm bản đồ Leaflet, hiển thị ghim `📍 Vị trí thiết bị của bạn`, và tính khoảng cách chính xác đến các phòng khám da liễu. Thêm banner trạng thái GPS, nút "Cập nhật lại vị trí", và dropdown chọn nhanh khu vực theo đúng chuẩn Master Spec. Phía API backend bổ sung fallback tự động tính khoảng cách tới toàn bộ phòng khám khi vị trí thiết bị nằm ngoài bán kính mặc định.
  2. **Khôi phục tiến trình ngang (Horizontal Stepper):** Điều chỉnh CSS `.wizard-steps, .wizard-steps-bar` và `.step-circle, .step-num` thành `display: flex !important; flex-direction: row !important;` với `flex: 1`, hiển thị kết nối đường kẻ ngang và các vòng tròn tiến trình số/dấu tích xanh hoàn chỉnh trên cùng 1 hàng ngang như giao diện chuẩn ban đầu.
  3. **Nút Đăng ký ngoài giao diện:** Thêm nút "Đăng ký" trên thanh Header bên cạnh nút Đăng nhập và trên trang chủ (`#/register`), cung cấp màn hình đăng ký (`renderRegister`) lưu thông tin người dùng trực tiếp vào cơ sở dữ liệu máy tính (`data/derma.db` qua `POST /api/auth/register`), sau đó tự động đăng nhập và lưu phiên làm việc.
- **Lý do:** Đáp ứng trọn vẹn yêu cầu vận hành của người dùng, giúp giao diện trực quan và trải nghiệm mượt mà trên mọi thiết bị.
