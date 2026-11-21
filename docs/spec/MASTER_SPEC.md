# DERMACARE AGENT — MASTER BUILD SPEC (bản hợp nhất, v2)

> **Dành cho AI coding agent (Antigravity).** File này là bản hợp nhất của 3 nguồn: (1) `DermaCare_Agent.docx` (sự thật về sản phẩm: phạm vi, an toàn, kiến trúc, test T01–T10, bộ bằng chứng P1–P10), (2) `DERMACARE_AGENT_BUILD_SUPPLEMENT.pdf` (sự thật về triển khai: repo, schema, API, spec contract, phase), (3) **Hướng đi sản phẩm bản kết hợp** (tra cứu danh sách tình trạng da tương đồng + tìm phòng khám GPS + gói Verified Partner + Timeline + cấp/thu hồi quyền).
>
> **Thứ tự ưu tiên khi mâu thuẫn:** (a) an toàn y tế / quyền riêng tư thắng tất cả; (b) mục 1.4 (Bảng hợp nhất) thắng hai tài liệu gốc ở những điểm nó nêu; (c) chi tiết kỹ thuật trong file này thắng ghi chú chung chung trong docx.
>
> **Bản v2 đã điền sẵn 3 bộ dữ liệu seed:** Phụ lục B (cơ sở kiến thức 20 tình trạng da), Phụ lục C (safety rules), Phụ lục D (danh bạ cơ sở khám da liễu thật ở TP.HCM). Dữ liệu được soạn từ nguồn công khai (AAD, CDC, NIAMS/NIH, MedlinePlus, Mayo Clinic, Harvard Health, National Psoriasis Foundation, và trang thông tin/đặt khám tại Việt Nam) kèm URL nguồn. **Đây là bản soạn từ tài liệu, KHÔNG phải kết quả thẩm định của bác sĩ**: mọi mục vẫn `reviewed_by_clinician: false` cho tới khi một bác sĩ da liễu có chứng chỉ hành nghề duyệt và ký tên (mục 21). Agent KHÔNG được tự đổi cờ này thành `true`.
>
> **Bước đầu tiên của agent:** copy file này vào `docs/spec/MASTER_SPEC.md`, tạo `AGENTS.md` (< 6 KB) tóm tắt mục 0 + lệnh make + đường dẫn spec, rồi làm Phase 0a (mục 19).

---

## 0. QUY TẮC LÀM VIỆC CỦA AGENT

1. **Không hỏi lại người dùng những gì có thể tự quyết.** Chọn phương án mặc định trong file này, ghi vào `DECISIONS.md` (quyết định, lý do, phương án khác).
2. **Làm theo phase ở mục 19.** Mỗi phase: code → chạy test/gate → commit `feat(phase-N): ...` → cập nhật `PROGRESS.md`. Không sang phase sau khi gate phase trước chưa pass.
3. **Việc cần con người** (API key, tạo app Privy, faucet, tải dataset, bác sĩ duyệt nội dung, xác minh lại thông tin/toạ độ phòng khám) → KHÔNG bịa. Ghi vào `HUMAN_TODO.md` và dùng cơ chế fallback đã định nghĩa (mock / stub / ABSTAIN / dữ liệu synthetic) để dự án vẫn chạy được.
4. **SDK/thư viện thay đổi nhanh** (Privy, thirdweb, LangGraph, Next.js, Foundry, OpenZeppelin, react-leaflet, pgvector client): đọc tài liệu chính thức phiên bản hiện hành trước khi viết code, không dựa vào trí nhớ. Ghim phiên bản vào lockfile.
5. **Không bao giờ:**
   - commit secret hoặc ảnh y tế;
   - ghi PII / ảnh / triệu chứng / chẩn đoán / tên bệnh lên chain;
   - log ảnh hoặc nội dung triệu chứng;
   - để LLM tự chẩn đoán hoặc tự sinh danh sách bệnh;
   - hiển thị % mắc bệnh, điểm "Skin Score", mức nặng/nhẹ, hoặc mức độ cần khám khẩn cấp suy ra từ ảnh;
   - lưu toạ độ GPS chính xác của người dùng vào DB.
6. Mọi số liệu hiển thị phải có `provenance ∈ {ai_measured, user_reported, clinician_entered, synthetic}`.
7. Dữ liệu demo luôn gắn nhãn **SYNTHETIC / DEMO** trên UI và trong DB (`is_synthetic=true`). Phòng khám dùng để demo gói Partner là phòng khám **hư cấu**. Danh bạ ở Phụ lục D là cơ sở **thật**: chỉ được hiển thị dạng thông tin công khai (`listing_type='directory'`), **không bao giờ** gắn Partner/verified hay nút gửi hồ sơ cho các cơ sở này.
7b. Cơ sở kiến thức (Phụ lục B) và safety rules (Phụ lục C) luôn hiển thị badge "chưa được bác sĩ duyệt" khi `reviewed_by_clinician=false`; agent không được sửa nội dung y khoa tuỳ ý — chỉ nạp đúng dữ liệu phụ lục và test schema.
8. Khi tuyên bố "xong" phải kèm bằng chứng: đầu ra lệnh test thật, danh sách file đã tạo, những gì chưa làm. Không tắt test cho xanh, không xoá test fail.
9. Nếu một gate lỗi sau 3 lần sửa: ghi nguyên nhân vào `PROGRESS.md` mục "Blocked", dùng fallback, báo rõ phần nào là fallback, rồi đi tiếp.

---

## 1. SẢN PHẨM (BẢN HỢP NHẤT)

### 1.1 Định nghĩa

**DermaCare Agent** là web app *tra cứu biểu hiện da – theo dõi dài hạn – kết nối phòng khám da liễu gần nhất theo GPS*:

- Người dùng khai báo vùng da + triệu chứng, chụp ảnh chuẩn khung (kiểu eKYC), hệ thống đo các chỉ số hình ảnh có thể lặp lại và **liệt kê các tình trạng da có biểu hiện tương đồng (chỉ để tham khảo)**.
- Người dùng theo dõi tiến triển bằng Timeline (ảnh chụp cùng khung + nhật ký triệu chứng) và xuất báo cáo PDF cho bác sĩ.
- Người dùng tìm phòng khám da liễu gần nhất qua GPS; phòng khám mua gói **Verified Partner** được ưu tiên hiển thị và nhận hồ sơ + tư vấn trực tiếp.
- Người dùng toàn quyền cấp / thu hồi quyền xem hồ sơ; bằng chứng cấp/thu hồi được ghi lên Avalanche (chỉ commitment ngẫu nhiên, không dữ liệu sức khoẻ).

### 1.2 Nguyên tắc cốt lõi (bất biến)

1. Hệ thống **không chẩn đoán, không kê đơn, không khuyên ngưng thuốc**, không khẳng định lành/ác tính.
2. Danh sách tình trạng tương đồng: **không hiện %, không xếp hạng, không mức nặng/nhẹ, không mức độ cần khám**; luôn kèm câu "Chỉ để tham khảo, không phải chẩn đoán".
3. Danh sách đó chỉ sinh từ **Vector DB kiến thức** (pgvector) do người/bác sĩ duyệt — LLM không được tự đề xuất tên bệnh.
4. Không có "Skin Score" gộp. Mỗi chỉ số hiển thị riêng, kèm provenance + confidence + model_version.
5. Tách rõ 4 nguồn dữ liệu: AI-measured / User-reported / Clinician-entered / Synthetic.
6. Quyền truy cập thực tế do **DB/API (off-chain)** quyết định; blockchain chỉ là bằng chứng bổ trợ.
7. "Verified Partner" là gói dịch vụ thương mại của phòng khám, **không phải chứng nhận chất lượng y khoa**; UI phải ghi rõ "Hiển thị ưu tiên theo gói đối tác".

### 1.3 User Flow (6 bước)

| # | Bước | Chi tiết | Kết quả |
|---|------|----------|---------|
| 1 | Khai báo triệu chứng | Chọn vùng cơ thể (body map) + form triệu chứng trực quan (ngứa, đỏ, bong tróc, rỉ dịch, phồng rộp/mụn mủ, đau/rát, chảy máu, thời gian xuất hiện, lan rộng…). Form render từ YAML. | `symptom_entries` (provenance=user_reported) |
| 2 | Chụp ảnh chuẩn khung (eKYC) | Camera có khung hướng dẫn theo bộ phận (`getUserMedia` + fallback upload). Kiểm tra nhanh ở client rồi **Quality Gate** ở server (độ nét, sáng, loá, độ phân giải, khung). Ảnh mờ/tối → yêu cầu chụp lại ngay. | `image_assets`, `quality_reports` (PASS/RETAKE/REVIEW) |
| 3 | AI phân tích & truy vấn Vector DB | CV đo: diện tích vùng tổn thương, mật độ nốt (nếu có detector), màu/texture. Ghép với form → vector đặc trưng → truy vấn pgvector → trả **danh sách tình trạng tương đồng** (tham khảo). | `visual_measurements`, `similar_condition_results` |
| 4 | Tìm phòng khám gần nhất (GPS) | Lấy GPS qua trình duyệt (chỉ khi người dùng bấm), liệt kê phòng khám da liễu quanh đó. Partner đang hiệu lực hiển thị nổi bật + nút **"Gửi hồ sơ & Tư vấn ngay"**. | Danh sách phòng khám + bản đồ |
| 5 | Chia sẻ hồ sơ & bác sĩ tư vấn | Người dùng chọn scope + thời hạn → hệ thống cấp quyền (ghi bằng chứng lên Avalanche). Bác sĩ của phòng khám xem ảnh gốc + báo cáo trên Doctor Dashboard, nhắn tin tư vấn, hẹn lịch theo dõi. | `consents`, `consult_messages`, `appointments` |
| 6 | Theo dõi tiến triển (Timeline) | Nhắc chụp lại đúng khung cũ; Comparator kiểm tra tương thích; hiển thị thay đổi từng chỉ số. Khám xong bấm **Thu hồi quyền** → bác sĩ bị 403 ngay ở request kế tiếp. | `comparisons`, timeline, `reminders` |

### 1.4 BẢNG HỢP NHẤT — các điểm hai tài liệu gốc chưa khớp với hướng đi mới

| ID | Vấn đề | Quyết định (agent áp dụng) |
|----|--------|----------------------------|
| U1 | docx: "không hiển thị tên bệnh khi `diagnosis_status=unknown`". Hướng mới: hiện danh sách tình trạng tương đồng. | Tên tình trạng **chỉ** được hiển thị trong component `SimilarConditionsPanel` (có disclaimer cố định, không %, không thứ hạng, thứ tự theo alphabet). Cấm xuất hiện ở tiêu đề case, header báo cáo, timeline, notification, tên file PDF. Test quét chuỗi có whitelist đúng component này. |
| U2 | Hướng mới: "không đánh giá mức độ cần khám". docx/supplement: có Safety Router (URGENT_MESSAGE). | **Giữ Safety Router** (an toàn thắng). Nó KHÔNG đánh giá ảnh; chỉ kích hoạt khi người dùng tự khai các dấu hiệu red flag trong form (sốt + phát ban lan nhanh, sưng mặt/môi/khó thở, phồng rộp quanh mắt/miệng/sinh dục, đau dữ dội lan rộng kèm đỏ nóng) bằng rule xác định. Thông điệp chung "đến cơ sở y tế/cấp cứu ngay (115)", không nêu tên bệnh, không mức độ. |
| U3 | docx: cần chọn `profile` (acne/eczema/psoriasis/other) khi tạo case. Hướng mới: luồng bắt đầu từ vùng da + triệu chứng. | Case mới mặc định `profile_type=other`, `diagnosis_status=unknown`. Nếu người dùng nói "đã được bác sĩ chẩn đoán" thì cho chọn `acne/eczema/psoriasis` để dùng form theo dõi chuyên biệt. Profile `other` vẫn hiển thị từng điểm đo trên timeline khi COMPARABLE nhưng **không vẽ đường trend**, luôn `requires_clinician_review=true`. |
| U4 | Supplement không có Vector DB. | Thêm **pgvector** (extension của PostgreSQL, không thêm dịch vụ mới) + bảng `knowledge_conditions` (mục 10). Embedding mặc định là vector đặc trưng xác định (không cần model/GPU/API key). |
| U5 | Supplement không có GPS / phòng khám / Partner. | Thêm module mục 11 (clinics, partner_subscriptions, tìm gần nhất bằng haversine, bản đồ Leaflet + OpenStreetMap). Đây là **công nghệ bổ sung được phép duy nhất** ngoài danh sách gốc (ghi `DECISIONS.md`). |
| U6 | Consent cũ nhắm tới `recipient_user_id` (một bác sĩ). Hướng mới: gửi cho phòng khám. | Consent nhắm tới `recipient_clinic_id` (và tuỳ chọn `recipient_user_id`). Bác sĩ `verified` thuộc phòng khám đó, phòng khám có Partner đang hiệu lực, thì xem được trong scope + hạn. Commitment on-chain vẫn gồm recipient trong hash off-chain (không lộ quan hệ bệnh nhân–phòng khám). |
| U7 | Hướng mới: Partner dùng Avalanche. | Mua gói Partner = giao dịch `TestSettlement.payInvoiceWithPermit` bằng **test token** trên Fuji (`invoice_type='partner_package'`). Khi `CONFIRMED` → bật `partner_until`. Gắn nhãn "TEST SETTLEMENT — không phải thanh toán thật". Không cần contract mới. |
| U8 | Hướng mới: "tư vấn trực tiếp". | Thêm `consult_messages` (text-only, chỉ khi consent active, thuộc dữ liệu sức khoẻ: qua service layer + audit, không log nội dung). |
| U9 | Hướng mới: GPS. | Toạ độ chỉ gửi trong request tìm kiếm, **không lưu DB, không log chi tiết** (làm tròn 2 chữ số thập phân khi log). Nếu từ chối GPS: chọn tỉnh/quận thủ công. |

---

## 2. DEFINITION OF DONE (toàn dự án)

Trên máy sạch (Windows+WSL2 hoặc macOS/Linux):

```bash
git clone <repo> && cd dermacare
cp .env.example .env     # điền tối thiểu: APP_MASTER_KEY, JWT_SECRET (script sinh sẵn)
make bootstrap           # cài deps, chạy infra (postgres+pgvector/redis/minio), migrate, seed
make dev                 # chạy api + worker + web
make test                # api, vision, contracts, web unit, e2e smoke
```

Kết quả bắt buộc:

- `http://localhost:3000` mở được; đăng nhập 3 tài khoản seed: `patient@demo.test`, `doctor@demo.test`, `admin@demo.test` (mật khẩu trong README, chỉ cho dev).
- Chạy trọn luồng: khai báo triệu chứng → chụp/tải ảnh → quality gate → phân tích → danh sách tình trạng tương đồng → tìm phòng khám GPS → gửi hồ sơ (consent) → bác sĩ xem + tư vấn + review → timeline → report PDF → thu hồi → bác sĩ bị 403.
- Chạy được không cần API key ngoài: `AUTH_MODE=local`, `WALLET_MODE=local-dev`, `CHAIN_MODE=mock`, `LLM_PROVIDER=none`. Khi có key thật và `CHAIN_MODE=fuji` thì giao dịch thật lên Avalanche Fuji.
- `make test` xanh; 10 test T01–T10 có test tự động (mục 18).

---

## 3. QUYẾT ĐỊNH KỸ THUẬT ĐÃ CHỐT

| Chủ đề | Quyết định | Lý do |
|--------|-----------|-------|
| Repo | Monorepo: `apps/web`, `apps/api`, `packages/contracts`, `ml/`, `docs/`, `infra/` | Một agent làm xuyên suốt |
| Chạy dev | Infra (Postgres+pgvector, Redis, MinIO) bằng docker compose; api/web/worker chạy native từ terminal | Tránh khó build native trong container trên Windows |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2 + Alembic, Pydantic v2, uv hoặc pip-tools | Theo docx |
| Frontend | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui, next-intl (vi mặc định, en), Recharts, **react-leaflet + OpenStreetMap** | Theo docx + GPS map |
| DB | PostgreSQL 16 + **pgvector** (image `pgvector/pgvector:pg16`) | Vector DB cho tra cứu tương đồng |
| Auth | Privy (email/Google + embedded wallet), backend verify access token (JWKS) rồi map sang `users`. Fallback: `AUTH_MODE=local` = email+mật khẩu (argon2) + JWT | Chạy được khi chưa có Privy key |
| Role | Lưu ở DB (`users.role`), KHÔNG tin role từ token/client | Chống leo quyền |
| Vision | OpenCV + NumPy + MediaPipe + imagehash (heuristic, không GPU, không dataset). PyTorch là optional extra (`pip install .[ml]`) | Dataset/weights không có sẵn |
| Embedding | Mặc định `FeatureVectorEmbedder` (xác định, 64 chiều). Tuỳ chọn extra `[text]`: sentence-transformers đa ngôn ngữ cho mô tả tự do | Không phụ thuộc API ngoài |
| LLM | Interface `LLMProvider`: `none` (mặc định, template-only), `gemini`, `anthropic`, `openai` | Không phụ thuộc 1 nhà cung cấp |
| Agent | LangGraph StateGraph; mọi node an toàn là code xác định | Theo docx |
| Queue | Redis + RQ (worker) + RQ-scheduler/APScheduler cho reminder | Đơn giản hơn Celery |
| Lưu ảnh | Upload qua backend: validate → strip EXIF (re-encode Pillow) → mã hoá AES-256-GCM (DEK riêng/ảnh, bọc bằng `APP_MASTER_KEY`) → MinIO. Đọc ảnh qua `GET /api/images/{id}/content?token=` với token JWT 60 giây | "Signed URL ngắn hạn", dễ chạy local |
| PDF | reportlab (thuần Python, chạy tốt trên Windows) | Tránh WeasyPrint/GTK |
| Chain | Solidity ^0.8.24 + Foundry + OpenZeppelin v5; Avalanche Fuji C-Chain (chainId 43113) | Theo docx |
| Gas | Backend relayer trả gas; user chỉ ký EIP-712 | Đơn giản, kiểm soát chi phí |
| Chain mode | `CHAIN_MODE=mock \| anvil \| fuji` | Dev/test không cần faucet |
| Windows | Làm trong WSL2; Foundry chạy trong WSL2 | Foundry hỗ trợ Windows qua WSL |

> Xác minh khi có mạng: Fuji RPC công khai `https://api.avax-test.network/ext/bc/C/rpc`, explorer testnet, faucet chính thức của Avalanche Builder Hub.

---

## 4. CẤU TRÚC REPO

```
dermacare/
├─ README.md DECISIONS.md PROGRESS.md HUMAN_TODO.md AGENTS.md Makefile .env.example
├─ .gitattributes (* text=auto eol=lf)  .editorconfig  .agents/workflows/{resume,phase-next,gate-check,release}.md
├─ infra/docker-compose.yml   # postgres(pgvector), redis, minio, (anvil optional); docker-compose.prod.yml
├─ apps/
│  ├─ api/
│  │  ├─ pyproject.toml alembic.ini Dockerfile Dockerfile.worker
│  │  ├─ app/
│  │  │  ├─ main.py config.py deps.py errors.py
│  │  │  ├─ core/ (security.py crypto.py audit.py rbac.py storage.py logging.py)
│  │  │  ├─ models/  schemas/
│  │  │  ├─ routers/ (auth cases observations images symptoms timeline reports consents clinician admin
│  │  │  │            reminders notifications wallet chain lookup clinics partner consults appointments me)
│  │  │  ├─ services/ (quality.py vision_client.py comparator.py reports.py consent.py
│  │  │  │            lookup.py embedder.py clinics.py partner.py chain/)
│  │  │  ├─ agent/ (state.py graph.py nodes/ tools.py safety_rules.yaml llm/ templates/)
│  │  │  ├─ profiles/ (intake_general.yaml acne.yaml eczema.yaml psoriasis.yaml other.yaml)
│  │  │  ├─ knowledge/ (conditions.yaml  # Phụ lục B; reviewed_by_clinician=false)
│  │  │  ├─ data/ (clinics_directory.yaml  # Phụ lục D, cơ sở thật; clinics_demo.yaml  # hư cấu)
│  │  │  └─ worker/ (jobs.py scheduler.py)
│  │  ├─ migrations/ scripts/ (seed.py gen_keys.py create_admin.py backup.sh restore.sh geocode_clinics.py kb_review.py) tests/
│  └─ web/  # Next.js
│     ├─ src/app/[locale]/(public|patient|doctor|admin)/...
│     ├─ src/components/ src/lib/ src/messages/{vi,en}.json
│     └─ tests/ (playwright)
├─ packages/contracts/   # Foundry
│  ├─ src/ (ConsentRegistry.sol DermaTestToken.sol TestSettlement.sol)
│  ├─ test/ script/Deploy.s.sol foundry.toml  deployments/fuji.json  abi/
├─ ml/
│  ├─ vision/ (quality.py roi.py segment.py compare.py acne_detector.py thresholds.yaml)
│  ├─ eval/ (calibrate_quality.py eval_segmentation.py eval_lookup.py)
│  ├─ train/ (train_acne.py README.md)   # viết sẵn, KHÔNG tự chạy
│  ├─ fixtures/   # ảnh synthetic do agent tự sinh
│  └─ MODEL_CARD.md DATASET_REGISTER.md
└─ docs/ (spec/ ARCHITECTURE.md OPENAPI.json USER_GUIDE.md DOCTOR_GUIDE.md ADMIN_GUIDE.md RUNBOOK.md
          SECURITY_PRIVACY.md RELEASE_NOTES.md TEST_REPORT.md BLOCKCHAIN_EVIDENCE.md DEPLOY.md
          DEMO_SCRIPT.md PILOT_PROTOCOL.md RELEASE_CHECKLIST.md)
```

`ml/vision` là package Python dùng chung; `apps/api` import trực tiếp (monolith), bọc sau interface `VisionService` để tách được sau.

---

## 5. MÔI TRƯỜNG

`.env.example` (agent tạo đầy đủ, có comment):

```env
# --- core ---
APP_ENV=dev
APP_MASTER_KEY=            # 32 bytes base64, sinh bằng scripts/gen_keys.py
JWT_SECRET=
DATABASE_URL=postgresql+psycopg://derma:derma@localhost:5432/derma
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minio
S3_SECRET_KEY=minio12345
S3_BUCKET=derma-private
# --- modes (mặc định chạy được không cần key ngoài) ---
AUTH_MODE=local            # local | privy
WALLET_MODE=local-dev      # local-dev | privy
CHAIN_MODE=mock            # mock | anvil | fuji
LLM_PROVIDER=none          # none | gemini | anthropic | openai
LLM_API_KEY=
# --- privy ---
PRIVY_APP_ID=
PRIVY_APP_SECRET=
NEXT_PUBLIC_PRIVY_APP_ID=
# --- chain ---
FUJI_RPC_URL=https://api.avax-test.network/ext/bc/C/rpc
CHAIN_ID=43113
RELAYER_PRIVATE_KEY=       # ví chỉ có AVAX testnet
CONSENT_REGISTRY_ADDRESS=
TEST_TOKEN_ADDRESS=
SETTLEMENT_ADDRESS=
RELAYER_DAILY_TX_CAP=200
# --- clinics / partner ---
CLINIC_SEARCH_DEFAULT_RADIUS_KM=10
CLINIC_SEARCH_MAX_RADIUS_KM=50
PARTNER_PACKAGE_PRICE_TEST=100
PARTNER_PACKAGE_DAYS=30
# --- lookup ---
LOOKUP_TOP_K=5
LOOKUP_MIN_COSINE=0.35     # uncalibrated default
```

**Makefile targets bắt buộc:** `bootstrap, infra-up, infra-down, migrate, seed, dev, api, worker, web, test, test-api, test-contracts, test-web, lint, deploy-fuji, openapi, reset`. Thêm `.vscode/launch.json` + `tasks.json` (F5 chạy api/web và debug). `make bootstrap` tự kiểm tra `python, node, pnpm, docker, forge` và in hướng dẫn cài nếu thiếu.

---

## 6. DATABASE SCHEMA (PostgreSQL, UUID pk, `created_at/updated_at` mọi bảng)

Enum dùng CHECK hoặc PG enum; JSONB cho trường linh hoạt; index trên mọi FK và `(case_id, captured_at)`. Bật `CREATE EXTENSION vector`. Thời gian lưu UTC.

| Bảng | Cột chính |
|------|-----------|
| users | id, email (unique), display_name, role {patient,clinician,admin}, auth_provider {local,privy}, auth_subject (unique), password_hash (null nếu privy), locale, status {active,disabled}, privacy_accepted_at, privacy_version, terms_version, terms_accepted_at |
| clinics | id, name, address_text, address_note, city, district, **lat, lng** (nullable, index), **geocode_status {pending,ok,failed,manual}**, phone, hours_note, **listing_type {directory,partner_candidate,partner}**, **source_url, source_checked_at**, status, verification_status {pending,verified,rejected}, **partner_until** (nullable), is_synthetic |
| clinician_profiles | user_id (pk,fk), clinic_id, **clinic_role {owner,doctor}**, license_no_enc, verification_status {pending,verified,rejected}, verified_by, verified_at |
| partner_subscriptions | id, clinic_id, tier ('verified_partner'), starts_at, ends_at, status {pending,active,expired,failed}, settlement_id |
| wallets | id, user_id (unique), address, provider {privy,local-dev}, terms_accepted_at, enc_key_ref (chỉ local-dev) |
| cases | id, patient_id, profile_type {acne,eczema,psoriasis,other}, diagnosis_status {clinician_diagnosed,unknown}, title, body_site, status {active,paused,closed}, cadence_days, clinician_id?, is_synthetic |
| observations | id, case_id, captured_at, workflow_state (mục 13), quality_status {PASS,RETAKE,REVIEW}, notes |
| image_assets | id, observation_id, view_type {overview,closeup}, object_key, sha256, phash, mime, width, height, dek_wrapped, exif_stripped, consent_scope_ref |
| roi_annotations | id, observation_id, image_id, method {user_drawn,face_landmarks,auto}, geometry JSONB, created_by |
| quality_reports | id, image_id, status, metrics JSONB, reasons JSONB, thresholds_version |
| visual_measurements | id, observation_id, metric_name, value, unit, confidence, model_version, provenance, roi_id, details JSONB |
| **knowledge_conditions** | id, slug (unique), name_vi, name_en, summary_vi/en, typical_features JSONB (key hợp lệ theo mục 10.2), body_sites[], **embedding vector(64)**, sources JSONB [{title,url,retrieved:bool}], reviewed_by_clinician (bool, mặc định false), reviewed_by, reviewed_at, version, active |
| **similar_condition_results** | id, observation_id, symptom_entry_id, embedder_version, kb_version, results JSONB [{condition_id, rank_internal}] (**không lưu/không trả điểm số**), abstain_reason?, created_at |
| comparisons | id, case_id, obs_from, obs_to, flag {COMPARABLE,PARTIAL,NOT_COMPARABLE}, reasons JSONB, deltas JSONB |
| symptom_entries | id, case_id, entered_at, form_version, answers JSONB, recall_window_days, provenance |
| clinician_reviews | id, case_id, clinician_id, note, clinician_scores JSONB [{name,value,scale}], plan JSONB, next_followup_at |
| consents | id, patient_id, case_id, **recipient_clinic_id**, recipient_user_id?, scope JSONB {images,measurements,symptoms,reports}, purpose, expires_at, status {active,revoked,expired}, revoked_at, commitment (bytes32 hex), nonce_enc, grant_tx_id, revoke_tx_id |
| **consult_messages** | id, consent_id, sender_id, body, sent_at, read_at |
| access_requests | id, clinician_id, patient_id, case_id?, message, status {pending,approved,denied} |
| appointments | id, case_id, clinician_id, patient_id, scheduled_at, status {proposed,confirmed,cancelled,done}, note |
| reminders | id, case_id, user_id, kind {capture,symptom,followup}, due_at, status {scheduled,sent,done,cancelled}, channel {in_app,email} |
| notifications | id, user_id, type, payload JSONB, read_at |
| reports | id, case_id, version, audience {patient,clinician}, content JSONB, pdf_object_key, generated_by {template,llm}, source_refs JSONB |
| agent_runs | id, case_id, observation_id, state_history JSONB, tool_calls JSONB, rule_hits JSONB (không ảnh/PII thô) |
| audit_events | id, actor_id, actor_role, action, resource_type, resource_id, result {allow,deny,error}, ip_hash, ts, anchor_batch_id? |
| audit_anchor_batches | id, merkle_root, event_count, chain_tx_id, created_at |
| chain_transactions | id, kind {consent_grant,consent_revoke,audit_anchor,settlement}, idempotency_key (UNIQUE), status {CREATED,SIGNED,SUBMITTED,CONFIRMED,FAILED,TIMEOUT}, tx_hash, chain_id, error, attempts, block_number, confirmed_at |
| settlements | id, invoice_ref (bytes32), invoice_type {partner_package,demo}, patient_id?, clinic_id, amount_test (numeric), status, chain_tx_id |
| model_registry | id, name, version, metrics JSONB, card_path, active |

Tất cả bảng chứa dữ liệu sức khoẻ (cases, observations, image_assets, symptom_entries, visual_measurements, similar_condition_results, consult_messages, reports, clinician_reviews): **chỉ truy cập qua service layer có kiểm tra quyền + ghi `audit_events`**.

---

## 7. AUTH & RBAC

Đăng ký mặc định là `patient`. Bác sĩ đăng ký bằng form riêng → `role='clinician'`, `verification_status='pending'`, **không nhận consent / xem dữ liệu cho tới khi admin verify**. Phòng khám đăng ký → `clinics.verification_status='pending'` tới khi admin verify. Admin đầu tiên tạo bằng seed/CLI `scripts/create_admin.py`, không có API đăng ký admin.

| Hành động | patient | clinician | admin |
|-----------|---------|-----------|-------|
| CRUD case/observation/symptom của chính mình | ✓ | ✗ | ✗ |
| Xem ảnh/measurement/danh sách tương đồng của case | chủ case | chỉ khi consent active, còn hạn, đúng scope, đúng phòng khám, **Partner còn hiệu lực** | ✗ (chỉ metadata/audit) |
| Ghi review / clinician_score / consult message | ✗ (patient chỉ nhắn trong consult) | ✓ nếu consent active | ✗ |
| Cấp/thu hồi consent | ✓ (case của mình) | ✗ | ✗ |
| Gửi access request | ✗ | ✓ (verified) | ✗ |
| Mua gói Partner | ✗ | ✓ (`clinic_role=owner`, clinic verified) | ✗ |
| Duyệt clinician/clinic, quản lý user, xem audit | ✗ | ✗ | ✓ |
| Tìm phòng khám gần nhất | ✓ | ✓ | ✓ |

Vi phạm → 403 + ghi `audit_events` result=deny. Kiểm tra consent chạy **mỗi request** (cache ≤ 5 giây); revoke/expiry có hiệu lực ngay ở request kế tiếp. Rate limit: login 5/phút/IP, upload 20/giờ/user, clinic search 30/phút/user. Upload: whitelist MIME (jpeg/png/webp/heic→convert), tối đa 12 MB, kiểm magic bytes, giới hạn kích thước pixel.

**Quyền dữ liệu cá nhân:** `GET /me/export` (JSON + ảnh trong zip, async, link hết hạn 15 phút); `DELETE /me` (xoá/ẩn danh tài khoản + ảnh + triệu chứng; giữ `audit_events` đã ẩn danh; ghi rõ trong `SECURITY_PRIVACY.md` rằng giao dịch đã lên chain không xoá được vì chỉ chứa commitment ngẫu nhiên không PII). Retention: case đóng > 24 tháng thì nhắc xuất/xoá.

---

## 8. API (REST, prefix `/api`, JSON)

Lỗi thống nhất: `{"error":{"code":"CONSENT_REQUIRED","message":"...","details":{}}}`. Mã tối thiểu: `UNAUTHENTICATED, FORBIDDEN, NOT_FOUND, VALIDATION_ERROR, CONSENT_REQUIRED, CONSENT_EXPIRED, QUALITY_RETAKE, NOT_COMPARABLE, DUPLICATE_IMAGE, MODEL_UNAVAILABLE, CHAIN_PENDING, CHAIN_FAILED, RATE_LIMITED, PARTNER_REQUIRED, LOCATION_INVALID`.

| Nhóm | Endpoint |
|------|----------|
| Auth | `POST /auth/register` (patient), `POST /auth/register-clinician`, `POST /auth/login`, `POST /auth/privy/exchange`, `GET /me`, `POST /me/privacy-accept`, `PATCH /me`, `GET /me/export`, `DELETE /me` |
| Profiles/Forms | `GET /profiles` (form schema từ YAML, gồm `intake_general`), `GET /profiles/{type}` |
| Cases | `POST /cases`, `GET /cases`, `GET /cases/{id}`, `PATCH /cases/{id}`, `POST /cases/{id}/close` |
| Observations | `POST /cases/{id}/observations`, `GET /cases/{id}/observations`, `GET /observations/{id}` |
| Images | `POST /observations/{id}/images` (multipart), `GET /images/{id}/meta`, `POST /images/{id}/token` (60s), `GET /images/{id}/content?token=`, `DELETE /images/{id}` |
| Quality | `POST/GET /images/{id}/quality` |
| ROI | `PUT /observations/{id}/roi` |
| Analysis | `POST /observations/{id}/analyze` (async job), `GET /observations/{id}/analysis` |
| **Lookup** | `GET /observations/{id}/similar-conditions` → `{items:[{slug,name_vi,name_en,summary}], disclaimer, abstain_reason?}` (không có điểm số) |
| Symptoms | `POST/GET /cases/{id}/symptoms` |
| Timeline | `GET /cases/{id}/timeline?metric=`, `POST /cases/{id}/compare` |
| Reports | `POST /cases/{id}/report`, `GET /cases/{id}/reports`, `GET /reports/{id}/pdf` |
| Reminders/Notif | `GET/POST/PATCH /reminders`, `GET /notifications`, `POST /notifications/{id}/read` |
| **Clinics** | `GET /clinics/nearby?lat=&lng=&radius_km=&limit=` (partner trước, rồi theo khoảng cách), `GET /clinics/search?city=&district=` (khi không có GPS), `GET /clinics/{id}` |
| **Partner** | `GET /clinic/partner` (trạng thái), `POST /clinic/partner/purchase` (→ settlement test token), `GET /clinic/partner/invoices` |
| Consents | `POST /consents`, `GET /consents`, `GET /consents/{id}`, `DELETE /consents/{id}` (revoke), `GET /consents/{id}/chain` |
| **Consults** | `GET/POST /consents/{id}/messages` |
| Access req | `POST /clinician/access-requests`, `GET /access-requests`, `POST /access-requests/{id}/approve|deny` |
| Appointments | `POST/GET /appointments`, `PATCH /appointments/{id}` (bác sĩ đề xuất, bệnh nhân xác nhận; tự tạo reminder followup) |
| Clinician | `GET /clinician/patients`, `GET /clinician/cases/{id}`, `POST /clinician/cases/{id}/review`, `GET /clinician/cases/{id}/timeline` |
| Admin | `GET /admin/users`, `PATCH /admin/users/{id}`, `GET/POST /admin/clinics`, `GET /admin/clinicians/pending`, `POST /admin/clinicians/{id}/verify|reject`, `POST /admin/clinics/{id}/verify|reject`, `GET /admin/audit`, `GET /admin/system/health`, `GET /admin/agent-runs` (đã scrub) |
| Wallet | `POST /wallet/provision`, `GET /wallet`, `POST /wallet/sign-request` (EIP-712 payload) |
| Chain | `GET /chain/transactions`, `POST /chain/settlements/demo`, `GET /chain/audit-batches`, `GET /chain/verify/{event_id}` |
| Ops | `GET /health`, `GET /ready` |

`make openapi` xuất `docs/OPENAPI.json`; dùng nó sinh typed client cho web (`openapi-typescript`).

---

## 9. VISION — SPEC BASELINE (không cần dataset/weights)

```python
class VisionService(Protocol):
    def assess_quality(self, img, profile, site) -> QualityReport   # PASS/RETAKE/REVIEW + metrics + reasons
    def localize_roi(self, img, profile, site, user_roi=None) -> ROI
    def measure(self, img, roi, profile) -> list[Measurement]       # luôn kèm model_version, confidence, provenance
    def compare(self, a: ObservationData, b: ObservationData) -> Comparison
```

**Quality Gate** (ngưỡng ở `ml/vision/thresholds.yaml`, có version, ghi rõ "uncalibrated defaults"):

| Kiểm tra | Cách tính | RETAKE | REVIEW |
|----------|-----------|--------|--------|
| Độ nét | Resize cạnh dài về 1024; variance of Laplacian trên ROI (chưa có ROI thì vùng giữa ảnh) | < 60 | 60–100 |
| Phơi sáng | % pixel luminance < 12 hoặc > 243 trong ROI | > 25% | 12–25% |
| Loá | % pixel V>240 & S<30 | > 8% | — |
| Độ phân giải | cạnh ngắn | < 640 px | — |
| Khung | ROI area / ảnh | — | < 4% hoặc > 95% |
| Trùng ảnh | sha256 trùng → `DUPLICATE_IMAGE`; pHash Hamming ≤ 5 so với ảnh cùng case → cảnh báo | | |

Script `ml/eval/calibrate_quality.py`: đọc thư mục `acceptable/` và `retake/` do con người gán nhãn, xuất ngưỡng đề xuất + precision/recall + false accept/reject rate. Viết sẵn; việc gán nhãn ghi vào `HUMAN_TODO.md`.

**Client-side pre-check (eKYC):** component camera chạy nhanh trên canvas (Laplacian xấp xỉ + histogram sáng) để báo "mờ/tối" trước khi upload; server vẫn là nguồn quyết định.

**ROI:** `acne`/mặt → MediaPipe Face Landmarker → 5 vùng (forehead, left_cheek, right_cheek, chin, nose) bằng đa giác từ landmark; không thấy mặt → user vẽ ROI. Các vùng khác (`eczema/psoriasis/other`, tay/chân/thân) → ROI do user vẽ (rect/polygon trên canvas), lưu toạ độ chuẩn hoá 0–1.

**Measure (`heuristic-lab-otsu-0.1`, nhãn "heuristic, không phải thang lâm sàng"):**

- `affected_area_ratio` = diện tích mask / diện tích ROI × 100. Mask: trong ROI chuyển LAB, lấy kênh a\*, chuẩn hoá theo median/MAD của ROI (chống lệch sáng), ngưỡng Otsu, morphological open/close, loại thành phần < 0.05% ROI. `confidence` = hàm của (độ tương phản histogram, quality score) trong [0,1], **không gọi là xác suất bệnh**.
- `color_descriptor` (LAB mean/std trong/ngoài mask), `texture_descriptor` (LBP/GLCM thống kê): hiển thị "tham khảo", không diễn giải.
- `lesion_count`, `lesion_density` (acne): dùng `AcneDetector`. Mặc định `NullDetector` → **ABSTAIN** lý do `no_weights`; UI hiện "chưa có model đếm tổn thương". Nếu có `ml/models/acne_det.*` hợp lệ + registry `active=true` thì dùng. Viết `ml/train/train_acne.py` (YOLO hoặc torchvision Faster R-CNN, group split, mAP@0.5:0.95, count MAE) + README, **không tự chạy**; HUMAN_TODO: tải ACNE04, kiểm tra license nguyên bản.
- `lesion_dispersion` (độ phân tán không gian của các thành phần trong mask), `component_count`: đặc trưng cho lookup (mục 10).
- Mọi measure chạy trong try/except → lỗi = `ABSTAIN` hoặc `MODEL_UNAVAILABLE`, **không bao giờ trả số cũ như mới** (T09).

**Comparability (cấu hình được):**

- `NOT_COMPARABLE` nếu: khác case, khác body_site, khác view_type, một trong hai ảnh quality ≠ PASS, hoặc ECC alignment thất bại.
- `PARTIAL` nếu: lệch median L\* của ROI > 15; diện tích ROI lệch > 35%; ECC correlation 0.6–0.8; khoảng cách thời gian < 12 giờ.
- `COMPARABLE` nếu ECC correlation ≥ 0.8 và các điều kiện trên đạt.
- Chỉ dùng affine/ECC hoặc keypoint homography; cấm warp phi tuyến mạnh. Trả `reasons[]` đọc được.
- Delta: ΔA = A_t − A_(t−1); ΔN (lesion count) chỉ khi COMPARABLE. PARTIAL: hiển thị kèm cảnh báo, không đưa vào trend.
- **Trend:** cần ≥ 3 điểm COMPARABLE; rolling median cửa sổ 3; không bao giờ ghi "tốt lên/xấu đi/khỏi" — chỉ "chỉ số X tăng/giảm trong ảnh".

**Fixtures:** agent tự sinh ảnh synthetic (nền màu da giả + đốm đỏ vẽ bằng numpy; mờ bằng Gaussian blur; tối/cháy sáng bằng gamma) cho T01–T03, T07. KHÔNG tải/commit ảnh bệnh nhân thật.

`ml/DATASET_REGISTER.md` (bảng có sẵn): SCIN, DermaCon-IN (CC BY-NC-SA — cấm mặc định cho thương mại), ACNE04, PAD-UFES-20, ISIC, DermNet; cột: nguồn, version, license, mục đích cho phép, hạn chế thương mại, trạng thái tải ("chưa tải"). `ml/MODEL_CARD.md`: mẫu điền sẵn cho `heuristic-lab-otsu-0.1`, metrics = "N/A — chưa có ground-truth, không bịa".

---

## 10. TRA CỨU TÌNH TRẠNG TƯƠNG ĐỒNG (VECTOR DB / pgvector)

### 10.1 Mục tiêu và giới hạn

Từ **form triệu chứng + đặc trưng ảnh**, trả về danh sách các tình trạng da có biểu hiện tương đồng để người dùng tham khảo trước khi đi khám. Đây là **truy vấn tương đồng trên cơ sở kiến thức**, không phải phân loại bệnh.

### 10.2 Không gian đặc trưng (64 chiều, cố định, có `embedder_version="fv-1"`)

Thứ tự chiều cố định theo danh sách key dưới đây (51 key dùng + 13 chiều dự phòng = 0). Mọi key trong `typical_features` của Phụ lục B **phải** nằm trong danh sách này (test schema).

| Nhóm | Key (mỗi key = 1 chiều) | Nguồn | Chuẩn hoá |
|------|-------------------------|-------|-----------|
| Vùng cơ thể (12) | `site_face, site_scalp, site_neck, site_trunk_front, site_back, site_arms, site_hands, site_legs, site_feet, site_folds, site_nails, site_other` | body map | 0/1 |
| Triệu chứng người dùng khai (28) | `itch, redness, scaling, dryness, oozing, crusting, blisters, pustules, papules, plaques, pain, burning, bleeding, cracking, spreading, recurrent, ring_shape, wheals, pale_patch, dark_patch, night_itch_contacts, one_sided_band, warty_surface, blackheads, contact_trigger, flushing, sweat_heat_trigger, greasy_scale` | form `intake_general` | 0/1; hoặc {0, 0.5, 1} cho none/some/many |
| Thời gian (5) | `onset_lt3d, onset_3_14d, onset_2_8w, onset_gt2m, onset_sudden` | form | one-hot / 0-1 |
| Đặc trưng ảnh (6) | `img_area, img_red_contrast, img_components, img_dispersion, img_texture, img_light_contrast` | `visual_measurements` (chỉ khi quality PASS) | clip + min-max theo hằng số trong `ml/vision/thresholds.yaml` (uncalibrated) |
| Dự phòng (13) | `reserved_00 … reserved_12` | — | 0 |

Ánh xạ form → key: câu hỏi "có hình vòng/tròn không?" → `ring_shape`; "nổi từng mảng phù, biến mất trong vài giờ?" → `wheals`; "mảng trắng nhạt/mất màu?" → `pale_patch`; "mảng sẫm màu?" → `dark_patch`; "ngứa nhiều về đêm và người ở cùng cũng ngứa?" → `night_itch_contacts`; "chỉ một bên cơ thể, thành dải?" → `one_sided_band`; "bề mặt sần như mụn cóc?" → `warty_surface`; "có nhân mụn đầu đen/trắng?" → `blackheads`; "xuất hiện sau khi tiếp xúc hoá chất/kim loại/mỹ phẩm/cây?" → `contact_trigger`; "đỏ bừng mặt từng đợt?" → `flushing`; "xuất hiện/nặng lên khi nóng, ra mồ hôi?" → `sweat_heat_trigger`; "vảy nhờn, vàng ở da đầu/mặt/nếp mũi má?" → `greasy_scale`.

Nếu ảnh không PASS hoặc measure ABSTAIN: các chiều ảnh = 0 và **chỉ dùng phần triệu chứng** (cờ `image_used=false`; UI nói rõ "kết quả chỉ dựa trên triệu chứng khai báo").

### 10.3 Knowledge base

- Nội dung nạp từ **Phụ lục B** (20 tình trạng phổ biến ở Việt Nam, soạn từ nguồn công khai có URL). Mỗi mục: `slug, name_vi/en, summary_vi/en` (chỉ mô tả **đặc điểm biểu hiện**, không điều trị), `body_sites`, `typical_features` (trọng số 0–1), `sources`.
- **Tất cả mặc định `reviewed_by_clinician=false`**; UI hiển thị badge "Nội dung tham khảo, chưa được bác sĩ duyệt". Chỉ khi bác sĩ da liễu duyệt (HUMAN_TODO) mới đặt `true` (qua CLI `scripts/kb_review.py --slug ... --reviewer ...`, ghi audit). Agent không tự đặt `true`.
- Trọng số `typical_features` là **ước lượng thiết kế** để truy vấn tương đồng, KHÔNG phải tần suất dịch tễ hay độ chắc chắn lâm sàng; ghi rõ trong `MODEL_CARD`/`KB_CARD`.
- Mục có thể nguy hiểm nếu trì hoãn (ví dụ zona gần mắt) **không dùng để "báo động"**; báo động chỉ do Safety Router (mục 12, Phụ lục C).
- Cấm trong KB: điều trị, thuốc, liều, tiên lượng, từ "bạn bị/mắc". Test schema quét các từ cấm (vi/en: "thuốc", "kem bôi", "điều trị bằng", "liều", "antibiotic", "steroid", "cream"…) trong `summary_*`.

### 10.4 Thuật toán truy vấn

1. Dựng vector `q` từ form + đo ảnh (10.2), chuẩn hoá L2.
2. SQL: `SELECT ... FROM knowledge_conditions WHERE active AND (body_sites && :sites OR body_sites = '{}') ORDER BY embedding <=> :q LIMIT :K` (cosine distance của pgvector; index HNSW hoặc ivfflat khi cần).
3. Lọc: giữ mục có cosine similarity ≥ `LOOKUP_MIN_COSINE` (uncalibrated). Không mục nào đạt → `abstain_reason="no_similar_match"` và UI hiện "Chưa tìm thấy biểu hiện tương đồng trong cơ sở dữ liệu; nên được bác sĩ đánh giá".
4. Vùng cơ thể chưa hỗ trợ / ảnh ngoài phạm vi → `ABSTAIN` (T07), không trả danh sách.
5. **Trả về không kèm điểm số.** Sắp xếp theo alphabet `name_vi` (không theo độ tương đồng để tránh bị hiểu là "khả năng mắc"). Điểm số chỉ lưu nội bộ để debug/eval trong `agent_runs` ở dạng thứ hạng (không hiển thị ra UI/API công khai).
6. Ghi `similar_condition_results` + audit.

### 10.5 UI bắt buộc (`SimilarConditionsPanel`)

- Tiêu đề: "Các tình trạng da có biểu hiện tương đồng (chỉ để tham khảo)".
- Disclaimer cố định: "Đây không phải chẩn đoán và không cho biết bạn có mắc bệnh. Hãy gặp bác sĩ da liễu để được đánh giá."
- Mỗi mục: tên + mô tả đặc điểm biểu hiện; **không** %, **không** thanh tiến trình, **không** màu đỏ/vàng/xanh theo mức độ.
- Dưới panel: nút "Tìm phòng khám gần tôi" (sang mục 11).
- Test (mục 18): quét DOM/JSON không có ký tự `%` cạnh tên bệnh, không có từ "mắc", "chẩn đoán là", "nặng", "nhẹ", "nguy hiểm".

### 10.6 Đánh giá

`ml/eval/eval_lookup.py`: (a) test sanity trên vector tổng hợp: mỗi mục KB truy vấn bằng chính prototype của nó phải nằm trong top-K; (b) khi có bộ ca do bác sĩ gán nhãn → hit@K, coverage, abstention rate. Chưa có ground-truth → ghi `N/A — chưa có dữ liệu`.

---

## 11. PHÒNG KHÁM GẦN NHẤT (GPS) & GÓI VERIFIED PARTNER

### 11.1 Tìm phòng khám

- Frontend gọi `navigator.geolocation.getCurrentPosition` **chỉ sau khi người dùng bấm** và đồng ý; từ chối → form chọn tỉnh/quận (`/clinics/search`).
- Backend `GET /clinics/nearby`: validate `lat∈[-90,90]`, `lng∈[-180,180]`, `radius_km ≤ CLINIC_SEARCH_MAX_RADIUS_KM`; lọc bounding box theo index (lat,lng) rồi tính haversine; chỉ trả phòng khám `verification_status='verified'`.
- Sắp xếp: **(1) phòng khám có `partner_until > now()` trước, (2) theo khoảng cách tăng dần.** Mỗi item: `id, name, address, distance_km, phone, is_partner, partner_label`. Khi `is_partner=true` kèm nhãn "Đối tác xác thực — hiển thị ưu tiên theo gói đối tác" và nút **"Gửi hồ sơ & Tư vấn ngay"**; không phải partner → chỉ hiện thông tin liên hệ/chỉ đường.
- Không lưu toạ độ người dùng; log chỉ làm tròn 2 chữ số thập phân.
- Bản đồ: react-leaflet + OSM tiles (ghi attribution; production cân nhắc nhà cung cấp tile có hợp đồng). Marker Partner nổi bật; danh sách và bản đồ đồng bộ.
- **Hai nguồn dữ liệu phòng khám, không được trộn lẫn:**
  1. `clinics_directory.yaml` (Phụ lục D): cơ sở khám da liễu **thật** ở TP.HCM, nguồn công khai có URL, `listing_type='directory'`. Hiển thị tên, địa chỉ, SĐT, giờ (kèm `source_checked_at` và dòng "Thông tin công khai, vui lòng gọi xác nhận"), nút chỉ đường. **Không** có Partner, không có nút gửi hồ sơ, không nhận consent (chưa hợp tác với DermaCare).
  2. `clinics_demo.yaml`: ~6 phòng khám **hư cấu** ("Phòng khám DEMO …", `is_synthetic=true`, toạ độ giả quanh TP.HCM) dùng để demo luồng Partner/consent/Doctor Dashboard.
- **Toạ độ cơ sở thật:** Phụ lục D để `lat/lng = null`, `geocode_status='pending'`. `scripts/geocode_clinics.py` tra Nominatim/OpenStreetMap theo `address_text` (tuân thủ usage policy: ≤1 request/giây, User-Agent riêng, cache kết quả, không chạy trong CI), lưu `geocode_status='ok'` kèm khoảng cách sai lệch so với kết quả thứ hai nếu có; kết quả không chắc → `failed` để con người nhập tay (`manual`). `/clinics/nearby` chỉ trả cơ sở có `geocode_status in (ok, manual)`; cơ sở chưa có toạ độ vẫn hiện ở `/clinics/search?city=&district=`. Agent **không tự điền toạ độ từ trí nhớ**.
- Địa chỉ hành chính TP.HCM đã thay đổi tên phường; lưu `address_text` (địa chỉ hiện hành theo nguồn) và `address_note` (tên cũ) để người dùng nhận ra địa điểm.

### 11.2 Gói Verified Partner

1. Điều kiện: clinic `verified` (admin duyệt) và người mua là `clinician` `owner` đã `verified`.
2. `POST /clinic/partner/purchase`: tạo `settlements(invoice_type='partner_package', invoice_ref=random bytes32)` + `partner_subscriptions(status=pending)` → pipeline chain (mục 15) gọi `TestSettlement.payInvoiceWithPermit` bằng DermaTestToken (owner ký permit; faucet token testnet).
3. Khi `chain_transactions.status=CONFIRMED` → `partner_subscriptions.status=active`, `clinics.partner_until = max(partner_until, now) + PARTNER_PACKAGE_DAYS`. `FAILED/TIMEOUT` → trạng thái `failed`, **không bật Partner** (T10).
4. Hết hạn: job định kỳ đặt `expired`; consent đang `active` vẫn **hết hiệu lực xem mới** khi Partner hết hạn? → Quyết định: consent đã cấp **vẫn còn hiệu lực đến hạn của consent** (quyền thuộc về người bệnh), nhưng clinic mất Partner thì không nhận consent **mới** và Doctor Dashboard khoá phần "inbox mới" (xem hồ sơ đã được cấp vẫn được). Ghi `DECISIONS.md`.
5. UI mua gói gắn nhãn "TEST SETTLEMENT — không phải thanh toán thật". Production ưu tiên thu VND qua đơn vị thanh toán; ghi `DEPLOY.md`.

### 11.3 Doctor Dashboard (mở khoá bởi Partner)

Hộp thư hồ sơ mới (consents active gửi tới phòng khám) → xem ảnh gốc (token 60s) + measurements + provenance + danh sách tương đồng + symptom → nhắn tin tư vấn → nhập review/plan/clinician_score → đề xuất lịch hẹn → theo dõi timeline sau khám. Mỗi truy cập ghi audit.

---

## 12. CONDITION PROFILE, FORM & SAFETY RULES

Mỗi profile là 1 YAML: `id, version, label_vi/en, body_sites[], capture_guide{overview,closeup}, symptom_form{fields[]}, cadence_days_default, measurements_enabled[], clinician_fields[], report_sections[], disclaimers[]`. Form do API trả, frontend render động (không hardcode). UI hiển thị câu: "Đây là trường theo dõi do nhóm thiết kế, KHÔNG phải thang đo đã xác thực."

- **intake_general** (bước 1 của luồng, dùng cho lookup và Safety Router): `body_region` (body map, chọn nhiều) → `site_*`; nhóm triệu chứng {none, some, many} hoặc bool ứng với 28 key triệu chứng ở mục 10.2 (câu hỏi bằng tiếng Việt đời thường, có icon/ví dụ); `onset` {<3 ngày, 3–14 ngày, 2–8 tuần, >2 tháng}; `onset_pattern` {đột ngột, từ từ}; `trigger_notes` (text, không dùng cho lookup, chỉ lưu); **câu hỏi an toàn** (đưa lên đầu form, bool): `fever`, `face_lip_swelling_or_breathing`, `blisters_mucosa` (phồng rộp quanh mắt/miệng/sinh dục), `skin_peeling_or_raw_large` (da bong thành mảng lớn/trầy xước rỉ dịch diện rộng), `purple_nonblanching_spots` (chấm/vết tím hoặc đen không mất khi ấn), `spreading_rapidly`, `severe_pain_hot_red_spreading`, `red_streak_from_lesion`, `new_medication_recent` (bắt đầu thuốc mới trong vài tuần gần đây), `immune_or_diabetes` (đang suy giảm miễn dịch hoặc đái tháo đường), `known_eczema` (đã biết có chàm/viêm da cơ địa), `known_psoriasis`, `joint_pain_or_stiffness`, `lesion_changing_fast_or_ulcer`, `rash_lasting_over_2_weeks`.
- **acne** (hằng tuần): sites {forehead,left_cheek,right_cheek,chin,other}; discomfort 0–10; new_lesions_estimate {none,few,some,many}; products_in_use; change_notes. Clinician: iga/gags (nhập tay, provenance=clinician_entered).
- **eczema** (2–3 ngày/lần, có thể hằng ngày): itch 0–10; sleep_disturbance 0–10; dryness 0–3; flaking 0–3; cracking, oozing, bleeding (bool); daily_impact 0–10. Feature flag `poem_enabled=false` (chỉ bật khi con người xác nhận quyền dùng POEM + bản dịch → HUMAN_TODO). Clinician: easi (nhập tay).
- **psoriasis** (hằng tuần): body_map region ids; itch 0–10; pain 0–10; scaling 0–3; joint_pain_or_stiffness bool; daily_impact 0–10. Clinician: bsa, pasi (nhập tay).
- **other** (hằng tuần): onset_date; change_since_last {none,larger,color_change,bleeding,painful,new_symptom}; description. Luôn `requires_clinician_review=true`; không vẽ trend.

**Safety rules** (`app/agent/safety_rules.yaml`, nạp nguyên văn từ **Phụ lục C**; xác định, không LLM; mỗi rule có `id, when, action, timeframe, message_vi/en, sources, reviewed_by_clinician:false`; cần bác sĩ duyệt trước khi dùng với người thật). `action ∈ {ROUTINE, CLINICIAN_REVIEW, URGENT_MESSAGE}`; riêng CLINICIAN_REVIEW có `timeframe ∈ {same_day, soon, routine}` — **chỉ suy ra từ câu trả lời red-flag người dùng tự khai, không từ ảnh**. Tóm tắt (chi tiết ở Phụ lục C):

- **URGENT_MESSAGE:** sốt kèm phát ban lan nhanh; sưng mặt/môi/khó thở; phồng rộp quanh mắt/miệng/sinh dục; đau dữ dội lan rộng kèm đỏ nóng. Thông điệp: "Hãy đến cơ sở y tế/cấp cứu ngay (Việt Nam: 115)". **Dừng luồng tự động**, không phân tích tiếp, không hiển thị danh sách tương đồng.
- **CLINICIAN_REVIEW:** rỉ dịch/chảy máu kèm đau tăng; tổn thương thay đổi nhanh/loét/chảy máu (profile other); đau khớp (psoriasis); ảnh REVIEW / model ABSTAIN; ảnh không tương thích nhiều lần → gợi ý "nên để bác sĩ xem hồ sơ" + nút tìm phòng khám.
- **ROUTINE:** còn lại.

Thông điệp rule chỉ dùng ngôn ngữ trung tính, không nêu tên bệnh, không mức nặng/nhẹ.

---

## 13. AGENT WORKFLOW (LangGraph)

State: `{case_id, observation_id, profile, consent_ok, quality, roi, measurements[], comparison, symptom_summary, similar_conditions, rule_hits[], workflow_state, report_draft, errors[]}`.

`workflow_state` (enum, lưu ở `observations`): `DRAFT → AWAITING_CAPTURE → QUALITY_REJECTED | READY_FOR_ANALYSIS → OBSERVATION_CREATED → NEEDS_REVIEW | TIMELINE_UPDATED → REPORT_READY`. Chuyển trạng thái chỉ qua một hàm `transition()` có bảng cho phép + test.

Node: `intake_consent → quality_gate → vision_observation → lookup_similar → comparator → profile_engine → safety_router → report_assistant → clinician_review_handoff`. **Safety router chạy trước `lookup_similar` hiển thị và trước report**, có quyền cắt luồng (URGENT).

Tool allowlist (LLM/graph chỉ gọi được): `create_observation, schedule_reminder, prepare_clinician_summary, get_timeline` (read-only). Mọi tool kiểm tra quyền như API thường và ghi `agent_runs.tool_calls`.

**LLM:**
- `LLM_PROVIDER=none` → báo cáo sinh từ template Jinja (đường chính để demo/test).
- Có LLM → chỉ diễn đạt lại dữ liệu có cấu trúc. System prompt cố định; dữ liệu người dùng trong khối `<untrusted_data>`; output ép JSON schema `{summary, items:[{text, source_ref_id}]}`. **LLM không được thêm/sửa tên tình trạng da.**
- Guard sau sinh: (1) mọi số trong output phải nằm trong tập số đầu vào; (2) mọi câu phải có `source_ref_id` hợp lệ; (3) quét từ cấm (chẩn đoán/đơn thuốc/"khỏi bệnh"/"nặng hơn"/"bạn bị"); vi phạm → bỏ output LLM, dùng template.
- Prompt injection trong ghi chú (T08): ghi chú không bao giờ ghép vào system prompt, không kích hoạt tool; có test payload "ignore previous instructions…".

**Reminder:** job lập lịch theo `cadence_days`; kênh `in_app` (bắt buộc) + `email` (tuỳ chọn qua SMTP, mặc định tắt); mỗi lần gửi ghi `notifications` + log. Nhắc chụp lại **đúng khung cũ** (hiển thị ảnh/overlay lần trước làm hướng dẫn).

---

## 14. REPORT

PDF (reportlab) + JSON. Cấu trúc: header (không nêu tên tình trạng da; tên file trung tính), banner "Không phải chẩn đoán", bảng phân tách 4 nguồn (AI-measured / User-reported / Clinician-entered / Synthetic), mục "Các tình trạng có biểu hiện tương đồng (tham khảo)" nếu có (không điểm số, kèm disclaimer; đây là mục duy nhất được nêu tên), timeline từng metric (không gộp điểm), danh sách "dữ liệu còn thiếu", danh sách ảnh không so sánh được kèm lý do, version + model_version, ngày tạo. Hai audience: patient, clinician. Không chứa địa chỉ ví.

---

## 15. BLOCKCHAIN (AVALANCHE) — SPEC CHI TIẾT

### 15.1 Nguyên tắc

Off-chain DB là nguồn quyền truy cập. On-chain chỉ giữ: commitment ngẫu nhiên, hành động (grant/revoke), expiry, Merkle root của batch audit, giao dịch settlement test (kể cả mua gói Partner). **Không đưa lên chain:** ảnh, URL, tên bệnh, triệu chứng, patient/doctor ID, email, địa chỉ ví của bác sĩ/recipient/phòng khám (trừ địa chỉ ví phòng khám bắt buộc cho settlement — dùng ví riêng của clinic, không liên kết hồ sơ bệnh nhân), ghi chú, report. Recipient nằm trong commitment (off-chain nonce), không là trường on-chain.

### 15.2 `ConsentRegistry.sol` (OpenZeppelin v5: EIP712, ECDSA, AccessControl, Pausable)

- `struct ConsentState { address patient; uint64 expiry; uint64 createdAt; bool revoked; }`; `mapping(bytes32 => ConsentState)`; `mapping(address => uint256) nonces`.
- EIP-712 domain: name `DermaCareConsent`, version `1`, chainId, verifyingContract. Typed data `ConsentAction(bytes32 commitment,uint8 action,uint64 expiry,uint256 nonce,uint256 deadline)`; action 1 = grant, 2 = revoke.
- `submitGrantWithSig(bytes32 commitment, uint64 expiry, uint256 deadline, bytes sig)` — `RELAYER_ROLE`; verify chữ ký, deadline, nonce; commitment chưa tồn tại; emit `ConsentGranted(commitment, patient, expiry)`.
- `submitRevokeWithSig(bytes32 commitment, uint256 deadline, bytes sig)` — chỉ patient gốc ký hợp lệ; `revoked=true`; emit `ConsentRevoked`.
- `anchorAudit(bytes32 merkleRoot, uint32 eventCount)` — `RELAYER_ROLE`; emit `AuditAnchored(merkleRoot, eventCount, uint64(block.timestamp))`.
- `isActive(bytes32) view returns (bool)`; `pause/unpause` cho `DEFAULT_ADMIN_ROLE`. Không hàm xoá, không selfdestruct/proxy.
- **Commitment** (tính ở backend): `keccak256(abi.encode(nonce32, consentId, recipientClinicId, recipientUserId, scopeHash, expiry))`, `nonce32` ngẫu nhiên 32 byte (CSPRNG), lưu mã hoá ở `consents.nonce_enc`. Cấm hash tất định từ dữ liệu ít entropy.

### 15.3 Settlement test (cũng dùng cho gói Partner)

- `DermaTestToken.sol`: ERC20 + ERC20Permit, `faucet()` mint tối đa N token/ngày/địa chỉ. Chỉ testnet.
- `TestSettlement.sol`: `payInvoiceWithPermit(bytes32 invoiceRef, address clinicWallet, uint256 amount, uint256 deadline, v, r, s)` (relayer gọi; payer ký permit); emit `InvoicePaid(invoiceRef, amount)`; `invoiceRef` bytes32 ngẫu nhiên, không PII. UI gắn "TEST SETTLEMENT — không phải thanh toán thật".

### 15.4 Merkle audit anchoring

Worker chạy mỗi 10 phút hoặc khi ≥ 50 audit event chưa anchor: `leaf = keccak256(event_id ‖ action ‖ ts ‖ random_salt)` (không PII); lưu salt + proof ở DB; gửi `anchorAudit(root,count)`; `/chain/verify/{event_id}` trả proof + tx hash. Không gửi giao dịch cho từng ảnh/triệu chứng.

### 15.5 Ví

- `WALLET_MODE=privy`: tạo embedded wallet chỉ khi user bật "Tính năng blockchain" và chấp nhận điều khoản ví (không tạo lúc đăng ký). Dùng Privy React SDK + API ký typed-data của embedded wallet (đọc docs Privy hiện hành).
- `WALLET_MODE=local-dev`: backend sinh keypair (`eth_account`), lưu private key mã hoá bằng `APP_MASTER_KEY`, ký thay user; UI badge "DEV WALLET".
- Địa chỉ ví không dùng làm patient ID; không hiển thị ví trong báo cáo.
- Bác sĩ chỉ nhận consent khi `clinician_profiles.verification_status='verified'` và phòng khám `verified` + Partner active (xác minh off-chain bởi admin).

### 15.6 Transaction pipeline (`app/services/chain/`)

Interface `ChainClient` với 3 implementation `MockChain`, `AnvilChain`, `FujiChain` (web3.py). `idempotency_key = sha256(kind ‖ resource_id ‖ action)` UNIQUE → gọi lại không tạo tx trùng. Máy trạng thái `CREATED → SIGNED → SUBMITTED → CONFIRMED | FAILED | TIMEOUT`; chỉ `CONFIRMED` khi receipt `status==1`. Retry backoff tối đa 3 lần; quá `RELAYER_DAILY_TX_CAP` → `RATE_LIMITED`. Tx lỗi: UI hiện pending/failed, **không báo thành công** (T10). **Revoke: DB chặn truy cập ngay, tx revoke gửi bất đồng bộ — không chờ chain.**

### 15.7 Foundry

- Test: grant hợp lệ; grant chữ ký sai; chữ ký hết hạn (deadline); replay (nonce); revoke bởi người lạ bị chặn; revoke xong `isActive=false`; anchor chỉ relayer; pause chặn grant; fuzz commitment/expiry; settlement permit hợp lệ/sai; faucet cap.
- `script/Deploy.s.sol` đọc env, ghi `deployments/fuji.json`; `make deploy-fuji` + lệnh verify (cần API key explorer → HUMAN_TODO). Xuất ABI vào `packages/contracts/abi/`.
- `docs/BLOCKCHAIN_EVIDENCE.md`: bảng contract address, tx hash grant/revoke/anchor/settlement/partner, link explorer, checklist "không PII on-chain" (liệt kê field on-chain từng event).

---

## 16. FRONTEND — MÀN HÌNH, TRẠNG THÁI, UX

Mỗi route có loading/empty/error state, responsive mobile-first, a11y cơ bản, vi/en (next-intl, vi mặc định). Thời gian hiển thị theo `Asia/Ho_Chi_Minh` (user đổi được).

- **Public:** `/`, `/login`, `/onboarding` (privacy + giới hạn công cụ + opt-in blockchain), `/privacy`, `/terms`, `/wallet-terms`, `/about-limits` (bản nháp vi+en, đầu trang ghi "BẢN NHÁP — cần rà soát pháp lý trước khi dùng thật").
- **Patient:**
  - `/start` — luồng tra cứu 6 bước dạng wizard: body map → form triệu chứng → chụp ảnh → kết quả (`SimilarConditionsPanel`) → phòng khám → chia sẻ.
  - `/cases`, `/cases/new` ("đã được bác sĩ chẩn đoán?" có/chưa → chọn profile), `/cases/[id]`, `/cases/[id]/capture` (khung eKYC theo bộ phận, `getUserMedia` + fallback upload, pre-check client rồi server), `/cases/[id]/roi` (canvas vẽ ROI / body map SVG), `/observations/[oid]` (quality + measure + provenance badge + similar conditions), `/cases/[id]/symptoms`, `/cases/[id]/timeline` (Recharts, từng metric riêng; trạng thái "không thể so sánh"), `/cases/[id]/report`.
  - `/clinics` — danh sách + bản đồ (GPS), nút "Gửi hồ sơ & Tư vấn ngay" cho Partner.
  - `/sharing` (cấp/thu hồi consent, chọn phòng khám + scope + hạn, trạng thái chain), `/consults/[consentId]` (nhắn tin), `/wallet`, `/notifications`, `/settings` (ngôn ngữ, xuất/xoá dữ liệu).
- **Doctor:** `/doctor/inbox` (hồ sơ mới — cần Partner), `/doctor/patients`, `/doctor/requests`, `/doctor/cases/[id]` (ảnh gốc, measurements + provenance, similar conditions, timeline, review/plan, clinician score), `/doctor/reviews`, `/doctor/partner` (trạng thái gói, mua gói test token), `/doctor/appointments`.
- **Admin:** `/admin/users`, `/admin/clinics`, `/admin/verification` (clinician + clinic), `/admin/audit`, `/admin/agent-runs`, `/admin/system`.

**Bắt buộc:** banner cố định "Công cụ tham khảo & theo dõi, không phải chẩn đoán"; badge provenance trên mọi số; watermark DEMO/SYNTHETIC khi `is_synthetic`; tên tình trạng da **chỉ** trong `SimilarConditionsPanel` và mục tương ứng của báo cáo; không có "điểm tổng"; không dùng từ "khỏi/nặng hơn/nguy hiểm/bạn bị"; lỗi thân thiện có nút thử lại. Thành phần: `ProvenanceBadge, QualityResultCard, ComparabilityBadge, SimilarConditionsPanel, ClinicMap, ClinicCard, PartnerBadge, ConsentCard, TxStatusPill, BodyMap, RoiCanvas, CaptureFrame, MetricChart, ConsultThread`.

---

## 17. SEED & DEMO

`make seed` tạo: 3 user (patient/doctor/admin), 2–3 clinic **hư cấu** (1 verified + Partner active có doctor verified; 1 verified không Partner; 1 pending), ~6 clinic hư cấu quanh TP.HCM cho bản đồ demo, nạp danh bạ **thật** Phụ lục D (`listing_type='directory'`, `is_synthetic=false`), nạp KB Phụ lục B và safety rules Phụ lục C, patient có 4 case (acne/eczema/psoriasis/other), mỗi case 4–5 observation synthetic (ảnh numpy, số đo mô phỏng), symptom entries, similar-condition results, 1 consent active + 1 revoked, vài consult message, notification, audit event, Mọi bản ghi demo `is_synthetic=true` (trừ KB và danh bạ thật, có nhãn riêng). Không dùng ảnh người thật. Seed chỉ chạy khi `ALLOW_SEED=true` hoặc `APP_ENV=dev`.

---

## 18. TEST — ÁNH XẠ T01–T10 SANG TEST TỰ ĐỘNG

| ID | Test | Khẳng định |
|----|------|-----------|
| T01 | `tests/test_quality.py::test_blur_dark_retake` | ảnh mờ/tối → RETAKE, không có visual_measurements trend |
| T02 | `test_compare.py::test_different_site` | NOT_COMPARABLE, deltas rỗng |
| T03 | `test_images.py::test_duplicate_hash` | DUPLICATE_IMAGE, không tạo observation lặp |
| T04 | `test_consent_upload.py` | chưa chấp nhận privacy/consent → upload bị chặn |
| T05 | `test_rbac.py::test_clinician_no_consent_403` | 403 + audit deny |
| T06 | `test_consent_lifecycle.py` | hết hạn/revoke → request kế tiếp 403 (CONSENT_EXPIRED) |
| T07 | `test_vision_scope.py` | ảnh ngoài phạm vi/không hỗ trợ → ABSTAIN/REVIEW, không có nhận định bệnh, không có danh sách tương đồng |
| T08 | `test_agent_injection.py` | ghi chú chứa lệnh → không gọi tool ngoài allowlist, output vẫn qua guard |
| T09 | `test_vision_down.py` | tắt vision → MODEL_UNAVAILABLE, API/UI không trả kết quả cũ |
| T10 | `test_chain_failure.py` | tx fail → FAILED/pending, không báo thành công, Partner **không** được bật |

**Test bổ sung bắt buộc:**
- RBAC matrix đầy đủ (mục 7); state machine hợp lệ/không hợp lệ; upload (magic bytes, quá cỡ); strip EXIF (ảnh test có GPS → sau lưu không còn); mã hoá ảnh round-trip; token ảnh hết hạn sau 60s; mỗi safety rule 1 test; LLM guard (số lạ/câu không nguồn bị loại).
- **Lookup:** prototype truy vấn trúng top-K; ảnh không PASS → chỉ dùng triệu chứng; KB rỗng/không đạt ngưỡng → abstain; API không có trường điểm số; URGENT_MESSAGE → không trả danh sách; quét chuỗi UI/API/PDF: không `%` cạnh tên tình trạng, không từ cấm, tên tình trạng chỉ ở component/mục whitelist.
- **Clinics/Partner:** haversine đúng (cặp toạ độ biết trước); partner xếp trước dù xa hơn; chỉ clinic verified xuất hiện; toạ độ không bị lưu DB/log; non-partner không nhận consent mới (`PARTNER_REQUIRED`); mua gói CONFIRMED → bật `partner_until`; FAILED → không bật; hết hạn → expired.
- **Dữ liệu y khoa/danh bạ:** (a) schema KB: mọi `typical_features` key ∈ danh sách 51 key mục 10.2, trọng số ∈ [0,1], mỗi mục có `sources` ≥ 1 và `reviewed_by_clinician=false`, `summary_*` không chứa từ điều trị/thuốc; (b) mỗi mục KB truy vấn bằng prototype của chính nó nằm trong top-K; (c) mỗi rule Phụ lục C có ≥ 1 test với input ví dụ và 1 test "không kích hoạt"; rule URGENT chặn danh sách tương đồng; thông điệp rule không chứa tên bệnh; (d) danh bạ Phụ lục D: mọi mục có `source_url`, `listing_type='directory'`, không `partner_until`, không `lat/lng` bịa (null cho tới khi geocode), API không trả nút gửi hồ sơ cho directory.
- no-PII-on-chain (quét mọi payload gửi chain: không email/ID/tên/tên bệnh/toạ độ); Foundry test mục 15.7; Playwright smoke luồng chính (gồm bước tìm phòng khám với GPS mock `context.setGeolocation`).
- CI `.github/workflows/ci.yml`: lint + test api/web/contracts, không cần secret.

---

## 19. THỨ TỰ BUILD & GATE (mỗi phase = 1 commit tag)

| Phase | Nội dung | Gate |
|-------|----------|------|
| 0a | `AGENTS.md`, `.agents/workflows/*`, PROGRESS/DECISIONS/HUMAN_TODO; chép spec vào `docs/spec/` | file tồn tại; `/resume` chạy được |
| 0 | Scaffold monorepo, docker compose (pgvector), Makefile, `.env.example`, CI, README, hello-world api/web | `make bootstrap && make dev` mở được web + `/health` |
| 1 | DB + Alembic (+ extension vector), auth (local + Privy exchange), RBAC, audit core, rate limit | `pytest tests/test_auth.py tests/test_rbac.py` |
| 2 | Profiles YAML (+ intake_general), cases, observations, symptoms, state machine | test cases/symptoms + state machine |
| 3 | Upload pipeline (validate, EXIF strip, encrypt, MinIO), quality gate, duplicate, token đọc ảnh | T01, T03, T04, upload tests |
| 4 | Vision baseline (ROI, heuristic measure, ABSTAIN, registry, model card) | T07, T09, vision tests |
| 4b | KB + embedder + lookup service/API + `eval_lookup.py` | lookup tests |
| 5 | Comparator, timeline, trend, report template + PDF | T02, report tests |
| 6 | LangGraph agent, safety rules, LLM interface + guard, reminders/notifications | T08, safety tests |
| 7 | Consent lifecycle (theo phòng khám), access request, consult messages, appointments, doctor APIs, admin APIs, clinics/nearby, partner state | T05, T06, clinics tests |
| 8 | Contracts (Foundry), chain client 3 mode, relayer, Merkle anchor, wallet, settlement + mua gói Partner | `forge test`, T10, no-PII test; (nếu có key) deploy Fuji |
| 9 | Frontend đầy đủ route mục 16, i18n, empty/loading/error, sinh API client, bản đồ | Playwright smoke xanh |
| 10 | Seed, docs (user/doctor/admin guide, runbook, security, release notes), test report, OPENAPI.json, backup/restore | `make test` xanh toàn bộ; mục 20 đủ |
| 11 | Dockerfile, deploy config, DEPLOY.md, DEMO_SCRIPT.md, PILOT_PROTOCOL.md, RELEASE_CHECKLIST.md, build prod chạy local `docker compose -f infra/docker-compose.prod.yml up` | build prod chạy; health xanh; mục 22–23 đủ |

Ưu tiên khi trễ: hoàn thiện luồng end-to-end hơn thêm tính năng. **Không thêm công nghệ ngoài danh sách** (trừ pgvector và react-leaflet đã chốt ở mục 1.4).

**Gợi ý phân việc nhóm 3 người (nếu chạy song song):** Người 1 — AI/Vision/Vector DB (mục 9, 10); Người 2 — Backend/GPS/Agent/PDF/consent (mục 6–8, 11, 13, 14); Người 3 — Frontend/Blockchain (mục 15, 16).

---

## 20. TÀI LIỆU PHẢI SINH RA

`README.md` (chạy từ VS Code từng bước, kể cả WSL2 cho Foundry), `docs/ARCHITECTURE.md` (sơ đồ mermaid), `OPENAPI.json`, `USER_GUIDE.md`, `DOCTOR_GUIDE.md`, `ADMIN_GUIDE.md`, `RUNBOOK.md` (backup/restore, xoay khoá, sự cố), `SECURITY_PRIVACY.md` (RBAC matrix, retention/xoá dữ liệu, EXIF, mã hoá, không PII on-chain, xử lý GPS), `RELEASE_NOTES.md`, `TEST_REPORT.md` (kết quả thật), `BLOCKCHAIN_EVIDENCE.md`, `DEPLOY.md`, `DEMO_SCRIPT.md`, `PILOT_PROTOCOL.md`, `RELEASE_CHECKLIST.md`, `ml/MODEL_CARD.md`, `ml/DATASET_REGISTER.md`. Số liệu chưa đo được ghi `N/A — chưa có dữ liệu`, không bịa metric.

---

## 21. VIỆC CẦN CON NGƯỜI (agent ghi vào `HUMAN_TODO.md`, không tự làm/bịa)

1. Tạo ứng dụng Privy → `PRIVY_APP_ID/SECRET`; cấu hình Google login; bật embedded wallet.
2. Tạo ví relayer, nạp AVAX testnet từ faucet chính thức → `RELAYER_PRIVATE_KEY` (không bao giờ dùng ví có tiền thật).
3. (Tuỳ chọn) API key LLM; API key explorer để verify contract.
4. Tải dataset (SCIN/ACNE04…) nếu muốn train/benchmark; đọc license từng bộ; không commit ảnh.
5. Gán nhãn bộ ảnh `acceptable/retake` để calibrate ngưỡng quality.
6. **Bác sĩ da liễu (có chứng chỉ hành nghề) duyệt và ký:** capture protocol, symptom form, **Phụ lục C (safety rules)**, **Phụ lục B (KB 20 mục + trọng số)**, nội dung báo cáo; xác nhận quyền dùng POEM nếu muốn bật. Lưu biên bản duyệt (tên, thời điểm, phiên bản) rồi mới chạy `kb_review.py`. Bản v2 đã được soạn từ tài liệu nhưng **chưa** qua bước này.
7. Thu cohort longitudinal thật (có consent/đạo đức) nếu muốn bằng chứng P6; nếu không giữ dữ liệu synthetic có nhãn.
8. Rà soát pháp lý (Luật BVDLCN 91/2025/QH15, NĐ 356/2025/NĐ-CP, phân loại phần mềm y tế; quảng cáo dịch vụ khám chữa bệnh liên quan nhãn "Verified Partner") trước khi dùng người thật/thương mại.
9. Tạo tài khoản hosting (Vercel + Render/Railway/Fly), managed Postgres (có pgvector)/Redis, bucket S3-compatible riêng tư; điền biến production; thêm domain vào Privy.
10. Quay video theo `DEMO_SCRIPT.md`; chụp bằng chứng Fuji Explorer.
11. Rà soát bản nháp trang pháp lý và consent form bởi người có chuyên môn.
12. Thử trên điện thoại thật (camera, ánh sáng, GPS) và ghi kết quả vào `TEST_REPORT.md`.
13. **Danh bạ phòng khám:** gọi điện/vào website xác nhận lại địa chỉ, SĐT, giờ khám của từng mục Phụ lục D; chạy `geocode_clinics.py` rồi kiểm tra toạ độ trên bản đồ; bổ sung cơ sở ở tỉnh/thành khác; ký thoả thuận thương mại nếu muốn một cơ sở thật trở thành Partner (khi đó mới chuyển `listing_type`); chọn nhà cung cấp bản đồ/tile cho production.
14. Quyết định chính sách độ tuổi người dùng (ví dụ yêu cầu từ 18 tuổi hoặc có người giám hộ) và rà soát pháp lý trước khi mở cho người thật.

---

## 22. CHECKLIST NGHIỆM THU CUỐI (agent tự tick trong `PROGRESS.md`)

- [ ] `make bootstrap && make dev && make test` pass trên máy sạch
- [ ] 4 profile tạo được case, form render từ YAML, báo cáo đúng profile
- [ ] Luồng tra cứu: triệu chứng → ảnh → quality gate → danh sách tương đồng (không %, không xếp hạng, có disclaimer)
- [ ] Quality gate / comparability / abstention hoạt động; không vẽ trend khi không tương thích
- [ ] Provenance trên mọi số; không "Skin Score"; không từ chẩn đoán trên UI (test quét chuỗi)
- [ ] Tìm phòng khám GPS: partner trước, rồi khoảng cách; không lưu toạ độ; fallback chọn quận
- [ ] Mua gói Partner bằng test token; FAILED không bật Partner
- [ ] Consent/revoke/expiry enforce off-chain ở request kế tiếp; bác sĩ ngoài phòng khám/ngoài scope bị 403
- [ ] `forge test` pass; `CHAIN_MODE=mock` và `anvil` chạy; `fuji` chạy khi có key; tx fail không báo thành công
- [ ] Quét payload chain: không PII/ảnh/chẩn đoán/tên bệnh/ID/toạ độ
- [ ] Ảnh mã hoá at-rest, EXIF đã strip, không ảnh trong log, token ảnh hết hạn 60s
- [ ] Seed synthetic đầy đủ, mọi màn hình demo có nhãn SYNTHETIC
- [ ] KB (Phụ lục B), safety rules (Phụ lục C), danh bạ (Phụ lục D) nạp đúng; badge "chưa được bác sĩ duyệt" hiển thị; cơ sở directory không có Partner/gửi hồ sơ
- [ ] Đủ tài liệu mục 20; `HUMAN_TODO.md` liệt kê rõ việc còn lại

---

## 23. WINDOWS, TRIỂN KHAI, VẬN HÀNH

**Windows:** làm toàn bộ trong WSL2 (VS Code Remote-WSL, project ở `~/dermacare`, KHÔNG ở `/mnt/c`); Docker Desktop bật WSL integration; thêm `.gitattributes` và `.editorconfig` (LF). Phiên bản gợi ý: Python 3.11/3.12, Node 20/22 LTS, pnpm, Docker Compose v2 — agent kiểm tra và ghi `DECISIONS.md`.

**Triển khai:** `apps/api/Dockerfile` (multi-stage, non-root, healthcheck) + worker cùng image khác command; web → Vercel; api + worker → chọn MỘT trong Render/Railway/Fly (ghi lý do); Postgres managed **có pgvector**, Redis managed; object storage S3-compatible riêng tư (R2/B2/S3) chỉ đổi biến `S3_*`. `docs/DEPLOY.md`: từng bước, biến production, `alembic upgrade head`, CORS chỉ cho domain web, domain trong Privy, `CHAIN_MODE=fuji`.

**Bảo mật HTTP:** HTTPS only, HSTS, CSP, X-Content-Type-Options, Referrer-Policy, `Permissions-Policy: geolocation=(self)`; cookie Secure/HttpOnly/SameSite; Bearer token trong bộ nhớ, refresh qua cookie httpOnly; giới hạn kích thước body.

**Production:** KHÔNG `AUTH_MODE=local` mặc định, KHÔNG `WALLET_MODE=local-dev`, KHÔNG seed demo trừ `ALLOW_SEED=true`; app từ chối khởi động nếu `APP_ENV=prod` mà `APP_MASTER_KEY/JWT_SECRET` rỗng hoặc là giá trị mẫu.

**Logging:** JSON có `request_id`; scrubber loại email/ảnh/nội dung triệu chứng/tin nhắn tư vấn/toạ độ chính xác khỏi log và error trace; `/admin/system/health` hiển thị DB/Redis/storage/chain/vision/LLM (không lộ secret); `scripts/backup.sh` (pg_dump + sao chép bucket) và `restore.sh` có test khôi phục trên dữ liệu seed.

---

## 24. GIAO THỨC LÀM VIỆC DÀI HẠN (chống mất ngữ cảnh)

1. Bước đầu: tạo `AGENTS.md` (< ~6 KB: tóm tắt sản phẩm, quy tắc mục 0, lệnh make, đường dẫn spec, giao thức này); chép `DermaCare_Agent.docx`, PDF supplement và file này vào `docs/spec/`.
2. Tạo `.agents/workflows/` (mỗi file < 12.000 ký tự): `resume.md` (đọc PROGRESS/DECISIONS/HUMAN_TODO, chạy gate gần nhất, báo trạng thái), `phase-next.md`, `gate-check.md`, `release.md` (checklist mục 22 + bằng chứng P1–P10).
3. Cuối mỗi phase và trước khi dừng: cập nhật `PROGRESS.md` (đã xong, đang dở, việc tiếp theo, lệnh chạy lại gate, lỗi đã biết) rồi commit.
4. Gate lỗi sau 3 lần sửa → mục "Blocked" + fallback; không giả vờ hoàn thành.
5. Mỗi phase dùng ngữ cảnh mới nếu có thể; chỉ đọc file liên quan.
6. Khi tuyên bố "xong": kèm bằng chứng (output test thật, danh sách file, phần chưa làm).

---

## 25. ÁNH XẠ BỘ BẰNG CHỨNG P1–P10

| Proof | Agent sinh ra | Con người làm |
|-------|---------------|---------------|
| P1 Product Walkthrough | `docs/DEMO_SCRIPT.md` (kịch bản từng cảnh, tài khoản + dữ liệu seed) | Quay video từ bản deploy |
| P2 Deployed Product | `DEPLOY.md`, 3 guide, `RELEASE_NOTES.md` | Deploy, điền URL |
| P3 Source Code | README, ARCHITECTURE, OPENAPI, migrations, commit theo phase | Đẩy lên GitHub (không ảnh y tế) |
| P4 Dataset Register | `ml/DATASET_REGISTER.md` | Đọc license, cập nhật trạng thái |
| P5 Model Card | `ml/MODEL_CARD.md`, `ml/eval/*` | Gán nhãn, chạy benchmark nếu muốn |
| P6 Longitudinal | Seed synthetic có nhãn + `docs/PILOT_PROTOCOL.md` | Thu cohort thật nếu có |
| P7 Agent Trace | `/admin/agent-runs` hoặc script xuất đã scrub | — |
| P8 Blockchain | `BLOCKCHAIN_EVIDENCE.md` (điền tx hash tự động sau deploy-fuji và demo) | Chạy với key thật, chụp explorer |
| P9 Security | `SECURITY_PRIVACY.md` + `TEST_REPORT.md` phần security | — |
| P10 QA | `TEST_REPORT.md`, `docs/RELEASE_CHECKLIST.md` | Thử trên điện thoại thật |

---

## PHỤ LỤC A — TUYÊN BỐ GIỚI HẠN (đưa vào README, `/about-limits`, đầu báo cáo PDF)

DermaCare Agent là công cụ **tham khảo và theo dõi**. Các chỉ số hình ảnh là phép đo kỹ thuật (heuristic), không phải thang lâm sàng. Danh sách tình trạng tương đồng được tạo từ cơ sở kiến thức tham khảo, **không phải chẩn đoán** và không cho biết người dùng có mắc bệnh. Mọi đánh giá, chẩn đoán, điều trị thuộc về bác sĩ có thẩm quyền. Sản phẩm chưa được thẩm định lâm sàng hay cấp phép là thiết bị/phần mềm y tế; không dùng trong tình huống khẩn cấp (Việt Nam: 115). Phòng khám "Verified Partner" hiển thị ưu tiên theo gói dịch vụ, không phải đánh giá chất lượng chuyên môn. Dữ liệu demo là dữ liệu tổng hợp (SYNTHETIC).

---

## PHỤ LỤC B — CƠ SỞ KIẾN THỨC TÌNH TRẠNG DA (nạp vào `app/knowledge/conditions.yaml`)

**Trạng thái:** bản soạn từ tài liệu công khai, **chưa được bác sĩ duyệt** (`reviewed_by_clinician: false` ở mọi mục). Mô tả chỉ nói về *đặc điểm biểu hiện*, không điều trị, không tiên lượng. `weights` là trọng số thiết kế cho truy vấn tương đồng (0–1), **không phải** tần suất dịch tễ. `sources[].retrieved=true` nghĩa là nội dung trang đã được đọc khi soạn; `false` nghĩa là chỉ ghi tên nguồn cần đối chiếu (agent/bác sĩ phải mở kiểm tra, không được tự suy ra URL). Key `weights` phải thuộc 51 key ở mục 10.2.

```yaml
kb_version: "kb-2026.11-draft1"
status: DRAFT_NOT_CLINICIAN_REVIEWED
disclaimer_vi: "Nội dung tham khảo, chưa được bác sĩ duyệt. Không phải chẩn đoán."
conditions:

- slug: acne_vulgaris
  name_vi: "Mụn trứng cá"
  name_en: "Acne"
  summary_vi: "Nhân mụn đầu đen hoặc đầu trắng, nốt sẩn đỏ và mụn mủ, thường ở mặt, ngực, lưng; kéo dài hoặc tái phát từng đợt, có thể để lại vết thâm."
  summary_en: "Blackheads or whiteheads, red bumps and pus-filled spots, usually on the face, chest and back; persistent or recurring, may leave dark marks."
  body_sites: [face, neck, trunk_front, back]
  weights: {site_face: 1, site_back: 0.6, site_trunk_front: 0.5, site_neck: 0.2, papules: 0.9, pustules: 0.8, blackheads: 0.9, redness: 0.5, recurrent: 0.6, pain: 0.3, dark_patch: 0.3, onset_gt2m: 0.6, onset_2_8w: 0.3, img_components: 0.8, img_dispersion: 0.6, img_red_contrast: 0.4}
  sources: [{title: "AAD – Acne (trang tổng quan/signs & symptoms)", url: null, retrieved: false}]

- slug: atopic_dermatitis
  name_vi: "Viêm da cơ địa (chàm thể tạng)"
  name_en: "Atopic dermatitis (eczema)"
  summary_vi: "Da rất ngứa, khô, đỏ hoặc sẫm màu, có thể bong vảy, nứt, rỉ dịch rồi đóng mày; hay ở nếp khuỷu, khoeo, cổ, cổ tay, mặt, và dễ tái phát. Ở người da sẫm có thể thấy sẩn xám đến nâu tím."
  summary_en: "Very itchy, dry, red or darker patches that may flake, crack, ooze and crust; often in elbow/knee folds, neck, wrists, face; tends to recur."
  body_sites: [face, neck, arms, hands, legs, folds]
  weights: {itch: 1, dryness: 0.9, redness: 0.6, scaling: 0.6, oozing: 0.4, crusting: 0.4, cracking: 0.4, plaques: 0.5, recurrent: 0.8, onset_gt2m: 0.7, site_arms: 0.8, site_hands: 0.6, site_neck: 0.5, site_face: 0.4, site_folds: 0.6, site_legs: 0.5, img_area: 0.5, img_texture: 0.5}
  sources:
    - {title: "AAD – Atopic dermatitis: signs and symptoms", url: "https://www.aad.org/public/diseases/eczema/types/atopic-dermatitis/symptoms", retrieved: true}
    - {title: "NIAMS/NIH – Atopic dermatitis", url: "https://www.niams.nih.gov/health_info/atopic_dermatitis", retrieved: true}
    - {title: "MedlinePlus – Atopic dermatitis", url: "https://medlineplus.gov/ency/article/000853.htm", retrieved: true}

- slug: plaque_psoriasis
  name_vi: "Vảy nến thể mảng"
  name_en: "Plaque psoriasis"
  summary_vi: "Mảng da dày, ranh giới rõ, phủ vảy trắng bạc (da sẫm có thể màu nâu tím/xám), hay ở khuỷu tay, đầu gối, lưng dưới, da đầu; có thể ngứa, đau, đổi màu móng; thường kéo dài và tái phát."
  summary_en: "Thick, well-defined patches covered with silvery scale (purple/brown/grey on darker skin), often on elbows, knees, lower back, scalp; may itch or hurt; nail changes possible; chronic and relapsing."
  body_sites: [scalp, arms, legs, back, trunk_front, nails, hands, feet]
  weights: {plaques: 1, scaling: 1, redness: 0.7, itch: 0.6, pain: 0.3, cracking: 0.3, recurrent: 0.8, onset_gt2m: 0.8, site_scalp: 0.8, site_arms: 0.8, site_legs: 0.8, site_back: 0.6, site_nails: 0.4, img_area: 0.6, img_texture: 0.6}
  sources:
    - {title: "AAD – Psoriasis: signs and symptoms", url: "https://www.aad.org/public/diseases/psoriasis/what/symptoms", retrieved: true}
    - {title: "AAD – Psoriasis overview", url: "https://www.aad.org/public/diseases/scaly-skin/psoriasis/what-is-psoriasis", retrieved: true}
    - {title: "MedlinePlus – Psoriasis", url: "https://medlineplus.gov/ency/article/000434.htm", retrieved: true}
    - {title: "National Psoriasis Foundation – Plaque psoriasis", url: "https://www.psoriasis.org/plaque", retrieved: true}

- slug: contact_dermatitis
  name_vi: "Viêm da tiếp xúc"
  name_en: "Contact dermatitis"
  summary_vi: "Vùng da đỏ, ngứa hoặc rát, có thể nổi mụn nước, rỉ dịch hoặc bong vảy, xuất hiện ở đúng vùng tiếp xúc với hoá chất, kim loại, mỹ phẩm hoặc cây cỏ; thường nổi sau khi tiếp xúc."
  summary_en: "Red, itchy or burning skin, sometimes with blisters, oozing or scaling, located where skin touched a chemical, metal, cosmetic or plant; appears after exposure."
  body_sites: [hands, face, arms, neck, other]
  weights: {contact_trigger: 1, itch: 0.9, redness: 0.8, blisters: 0.5, oozing: 0.4, burning: 0.5, scaling: 0.3, onset_lt3d: 0.5, onset_3_14d: 0.5, site_hands: 0.7, site_face: 0.4, site_arms: 0.4, site_neck: 0.3, site_other: 0.3, img_area: 0.4}
  sources: [{title: "AAD – Contact dermatitis (signs and symptoms)", url: null, retrieved: false}]

- slug: seborrheic_dermatitis
  name_vi: "Viêm da tiết bã"
  name_en: "Seborrheic dermatitis"
  summary_vi: "Mảng đỏ phủ vảy nhờn, vàng hoặc trắng ở da đầu, lông mày, hai bên cánh mũi, sau tai, giữa ngực; ngứa nhẹ đến vừa, hay tái phát."
  summary_en: "Red patches with greasy yellow or white scale on scalp, eyebrows, sides of the nose, behind ears, mid-chest; mild to moderate itch; recurs."
  body_sites: [scalp, face, trunk_front, folds]
  weights: {greasy_scale: 1, scaling: 0.8, redness: 0.6, itch: 0.5, recurrent: 0.8, onset_gt2m: 0.7, site_scalp: 1, site_face: 1, site_trunk_front: 0.3, site_folds: 0.3, img_red_contrast: 0.4}
  sources: [{title: "AAD – Seborrheic dermatitis (signs and symptoms)", url: null, retrieved: false}]

- slug: urticaria
  name_vi: "Mề đay (nổi mẩn phù)"
  name_en: "Hives (urticaria)"
  summary_vi: "Các mảng phù nổi cao, hồng hoặc đỏ, ngứa nhiều, có thể di chuyển và mờ đi trong vài giờ rồi nơi khác lại nổi; xuất hiện nhanh, có thể ở bất kỳ vùng nào."
  summary_en: "Raised pink or red itchy wheals that come and go within hours and may move around; appear quickly on any part of the body."
  body_sites: []
  weights: {wheals: 1, itch: 1, redness: 0.6, onset_sudden: 0.8, onset_lt3d: 0.7, spreading: 0.5, recurrent: 0.4, site_trunk_front: 0.6, site_arms: 0.6, site_legs: 0.6, site_back: 0.5, site_face: 0.4, img_dispersion: 0.7}
  sources: [{title: "AAD – Hives (signs and symptoms)", url: null, retrieved: false}]

- slug: tinea_ringworm
  name_vi: "Nấm da (hắc lào, nấm bẹn, nấm chân)"
  name_en: "Ringworm / tinea (body, groin, feet)"
  summary_vi: "Mảng tròn hoặc vòng, bờ đỏ hơi nổi và có vảy, giữa mảng thường nhạt hơn; ngứa; có thể lan rộng chậm; ở bẹn, kẽ chân hoặc lòng bàn chân có thể không thành vòng mà đỏ, bong, nứt."
  summary_en: "Round or ring-shaped patch with a slightly raised scaly red border and clearer centre; itchy; slowly enlarges; in groin or feet it may appear as red, peeling, cracked skin without a ring."
  body_sites: [trunk_front, back, arms, legs, folds, feet, hands, scalp, nails]
  weights: {ring_shape: 1, scaling: 0.8, itch: 0.9, redness: 0.6, plaques: 0.6, spreading: 0.5, sweat_heat_trigger: 0.5, onset_2_8w: 0.6, onset_3_14d: 0.4, site_folds: 0.8, site_feet: 0.8, site_trunk_front: 0.5, site_legs: 0.5, site_arms: 0.4, site_hands: 0.3, site_scalp: 0.3, site_nails: 0.2, img_dispersion: 0.3, img_texture: 0.4}
  sources:
    - {title: "CDC – Symptoms of ringworm", url: "https://www.cdc.gov/ringworm/signs-symptoms/", retrieved: true}
    - {title: "AAD – Ringworm: signs and symptoms", url: "https://www.aad.org/diseases/a-z/ringworm-symptoms", retrieved: true}
    - {title: "MedlinePlus – Ringworm, body", url: "https://medlineplus.gov/ency/article/000877.htm", retrieved: true}
    - {title: "Harvard Health – Ringworm (tinea)", url: "https://www.health.harvard.edu/a-to-z/ringworm-tinea-a-to-z", retrieved: true}
    - {title: "Mayo Clinic – Ringworm (body)", url: "https://www.mayoclinic.org/diseases-conditions/ringworm-body/diagnosis-treatment/drc-20353782", retrieved: true}

- slug: impetigo
  name_vi: "Chốc (nhiễm khuẩn da nông)"
  name_en: "Impetigo"
  summary_vi: "Mụn nước nhỏ hoặc bọng nước vỡ nhanh để lại vết đỏ rỉ dịch, rồi đóng vảy màu vàng mật ong; hay ở quanh mũi, miệng, tay, chân; ngứa hoặc đau nhẹ; có thể lan sang chỗ khác."
  summary_en: "Small blisters or larger bullae that burst quickly, leaving red oozing patches that form honey-coloured crusts; often around nose, mouth, hands and legs; mild itch or soreness; can spread."
  body_sites: [face, hands, arms, legs, other]
  weights: {crusting: 1, oozing: 0.7, blisters: 0.6, pustules: 0.4, redness: 0.6, itch: 0.5, pain: 0.3, spreading: 0.6, onset_3_14d: 0.6, onset_lt3d: 0.3, site_face: 1, site_hands: 0.5, site_arms: 0.5, site_legs: 0.4, img_components: 0.4}
  sources:
    - {title: "AAD – Impetigo: signs and symptoms", url: "https://www.aad.org/public/diseases/a-z/impetigo-symptoms", retrieved: true}
    - {title: "CDC – About impetigo", url: "https://cdc.gov/group-a-strep/about/impetigo.html", retrieved: true}
    - {title: "Harvard Health – Impetigo", url: "https://www.health.harvard.edu/a_to_z/impetigo-a-to-z", retrieved: true}

- slug: folliculitis
  name_vi: "Viêm nang lông"
  name_en: "Folliculitis"
  summary_vi: "Nhiều nốt đỏ nhỏ hoặc mụn mủ có sợi lông ở giữa, hơi ngứa hoặc đau, hay ở lưng, ngực, đùi, mông, vùng cạo lông; có thể nặng hơn khi nóng ẩm, mồ hôi."
  summary_en: "Many small red bumps or pustules centred on hair follicles, mildly itchy or tender, often on back, chest, thighs, buttocks or shaved areas; worse with heat and sweat."
  body_sites: [back, trunk_front, legs, folds, arms, face]
  weights: {pustules: 0.9, papules: 0.8, redness: 0.6, itch: 0.5, pain: 0.5, sweat_heat_trigger: 0.5, onset_3_14d: 0.5, site_back: 0.6, site_legs: 0.6, site_trunk_front: 0.5, site_folds: 0.5, site_arms: 0.4, site_face: 0.3, img_components: 0.8, img_dispersion: 0.6}
  sources: [{title: "AAD – Folliculitis (signs and symptoms)", url: null, retrieved: false}]

- slug: rosacea
  name_vi: "Trứng cá đỏ (rosacea)"
  name_en: "Rosacea"
  summary_vi: "Đỏ ở giữa mặt (má, mũi, trán, cằm), hay đỏ bừng từng đợt, có thể kèm nốt sẩn, mụn mủ, rát hoặc châm chích; kéo dài và tái diễn; không có nhân mụn đầu đen điển hình."
  summary_en: "Central facial redness (cheeks, nose, forehead, chin) with flushing episodes, sometimes bumps, pustules, burning or stinging; long-lasting and recurring; no typical blackheads."
  body_sites: [face]
  weights: {flushing: 1, redness: 1, papules: 0.6, pustules: 0.5, burning: 0.6, recurrent: 0.7, onset_gt2m: 0.8, contact_trigger: 0.2, site_face: 1, img_red_contrast: 0.7}
  sources: [{title: "AAD – Rosacea (signs and symptoms)", url: null, retrieved: false}]

- slug: vitiligo
  name_vi: "Bạch biến"
  name_en: "Vitiligo"
  summary_vi: "Mảng da mất màu trắng sữa, ranh giới rõ, thường không ngứa không bong vảy; hay ở mặt, bàn tay, nếp gấp, quanh miệng/mắt; xuất hiện dần và kéo dài."
  summary_en: "Sharply defined milk-white patches of lost pigment, usually without itch or scale; often on face, hands, folds, around mouth/eyes; appears gradually and persists."
  body_sites: [face, hands, folds, arms, feet]
  weights: {pale_patch: 1, onset_gt2m: 0.8, onset_2_8w: 0.3, site_hands: 0.6, site_face: 0.6, site_folds: 0.4, site_arms: 0.4, site_feet: 0.3, itch: 0.1, img_light_contrast: 1}
  sources: [{title: "AAD – Vitiligo (signs and symptoms)", url: null, retrieved: false}]

- slug: melasma
  name_vi: "Nám da"
  name_en: "Melasma"
  summary_vi: "Mảng sạm nâu đến xám đối xứng ở má, trán, môi trên, sống mũi; không ngứa, không bong vảy; kéo dài, có thể đậm lên khi nắng; hay gặp ở nữ."
  summary_en: "Symmetric brown to grey-brown patches on cheeks, forehead, upper lip, nose bridge; no itch or scale; long-lasting, may darken with sun."
  body_sites: [face]
  weights: {dark_patch: 1, onset_gt2m: 0.9, recurrent: 0.5, site_face: 1, itch: 0.0, redness: 0.0, img_light_contrast: 0.9}
  sources: [{title: "AAD – Melasma (signs and symptoms)", url: null, retrieved: false}]

- slug: warts
  name_vi: "Mụn cóc"
  name_en: "Warts"
  summary_vi: "Cục sần nhỏ bề mặt thô ráp như hoa lơ, có thể có chấm đen nhỏ; hay ở bàn tay, ngón tay, bàn chân (lòng bàn chân có thể đau khi đi); thường không ngứa; tồn tại lâu."
  summary_en: "Small rough cauliflower-like bumps, sometimes with tiny black dots; often on hands, fingers and feet (soles may hurt when walking); usually not itchy; long-standing."
  body_sites: [hands, feet, face, arms]
  weights: {warty_surface: 1, papules: 0.6, pain: 0.3, onset_gt2m: 0.6, onset_2_8w: 0.4, site_hands: 1, site_feet: 0.7, site_face: 0.3, site_arms: 0.3, itch: 0.1, img_components: 0.5}
  sources: [{title: "AAD – Warts (signs and symptoms)", url: null, retrieved: false}]

- slug: scabies
  name_vi: "Ghẻ"
  name_en: "Scabies"
  summary_vi: "Ngứa dữ dội nhất là về đêm, nốt sẩn nhỏ và đường hầm mảnh ở kẽ ngón tay, cổ tay, nách, vùng thắt lưng, bẹn; người sống cùng cũng thường bị ngứa; có thể trầy xước, đóng mày."
  summary_en: "Intense itch, worst at night, with small bumps and thin burrow lines between fingers, wrists, armpits, waist and groin; household contacts often itch too; scratching may cause crusts."
  body_sites: [hands, folds, trunk_front, arms, legs, feet]
  weights: {night_itch_contacts: 1, itch: 1, papules: 0.7, crusting: 0.4, redness: 0.4, spreading: 0.5, onset_2_8w: 0.6, onset_3_14d: 0.4, site_hands: 0.9, site_folds: 0.8, site_trunk_front: 0.5, site_arms: 0.5, site_legs: 0.3, site_feet: 0.3, img_components: 0.8, img_dispersion: 0.6}
  sources: [{title: "CDC – Scabies (symptoms)", url: null, retrieved: false}]

- slug: pityriasis_rosea
  name_vi: "Phấn hồng"
  name_en: "Pityriasis rosea"
  summary_vi: "Thường bắt đầu bằng một mảng hồng hình bầu dục lớn, vài ngày đến vài tuần sau xuất hiện nhiều mảng nhỏ hơn có viền vảy mỏng ở thân mình, lưng, đôi khi cánh tay đùi; ngứa nhẹ đến vừa."
  summary_en: "Often starts with one larger oval pink patch, followed days to weeks later by smaller patches with a thin scale edge on trunk and back, sometimes upper arms and thighs; mild to moderate itch."
  body_sites: [trunk_front, back, arms, legs, neck]
  weights: {plaques: 0.6, scaling: 0.6, redness: 0.6, itch: 0.5, onset_2_8w: 0.6, onset_3_14d: 0.4, site_trunk_front: 0.8, site_back: 0.8, site_arms: 0.4, site_legs: 0.3, site_neck: 0.2, img_area: 0.5, img_components: 0.5}
  sources: [{title: "AAD – Pityriasis rosea (signs and symptoms)", url: null, retrieved: false}]

- slug: keratosis_pilaris
  name_vi: "Sừng hoá nang lông (da gà)"
  name_en: "Keratosis pilaris"
  summary_vi: "Nhiều sẩn nhỏ cùng màu da hoặc hơi đỏ/sẫm, sờ thô ráp như da gà, ở mặt ngoài cánh tay, đùi, đôi khi má; da khô, ít ngứa; kéo dài nhiều năm."
  summary_en: "Many tiny skin-coloured, reddish or darker rough bumps like goose-flesh on outer arms, thighs, sometimes cheeks; dry skin, little itch; lasts for years."
  body_sites: [arms, legs, face, back]
  weights: {papules: 0.9, dryness: 0.8, scaling: 0.3, redness: 0.3, itch: 0.2, recurrent: 0.6, onset_gt2m: 1, site_arms: 1, site_legs: 0.8, site_face: 0.3, site_back: 0.1, img_components: 1, img_dispersion: 0.7}
  sources: [{title: "AAD – Keratosis pilaris (signs and symptoms)", url: null, retrieved: false}]

- slug: herpes_zoster
  name_vi: "Zona (giời leo)"
  name_en: "Shingles (herpes zoster)"
  summary_vi: "Đau rát hoặc châm chích trước, rồi nổi dải mụn nước đỏ chỉ ở một bên cơ thể (thường quanh thân mình hoặc một bên mặt), sau đó vỡ và đóng vảy."
  summary_en: "Burning or tingling pain first, then a band of red blisters on one side of the body (often around the trunk or one side of the face) that later burst and crust."
  body_sites: [trunk_front, back, face, neck]
  weights: {one_sided_band: 1, blisters: 0.9, pain: 1, burning: 0.8, redness: 0.6, itch: 0.3, crusting: 0.4, onset_3_14d: 0.6, onset_lt3d: 0.3, site_trunk_front: 0.6, site_back: 0.5, site_face: 0.3, site_neck: 0.2}
  sources: [{title: "AAD – Shingles (signs and symptoms)", url: null, retrieved: false}]

- slug: tinea_versicolor
  name_vi: "Lang ben"
  name_en: "Tinea versicolor"
  summary_vi: "Nhiều đốm hoặc mảng tròn nhỏ trắng nhạt hoặc nâu hồng, có vảy mịn, ở cổ, ngực, lưng, bả vai, cánh tay; ngứa nhẹ hoặc không; hay tái phát khi nóng ẩm, ra mồ hôi."
  summary_en: "Many small round pale or pink-brown spots or patches with fine scale on neck, chest, back, shoulders and arms; little or no itch; recurs in hot, humid weather."
  body_sites: [trunk_front, back, neck, arms]
  weights: {pale_patch: 0.6, dark_patch: 0.5, scaling: 0.5, itch: 0.3, sweat_heat_trigger: 0.8, recurrent: 0.7, onset_gt2m: 0.7, site_trunk_front: 0.9, site_back: 0.9, site_arms: 0.5, site_neck: 0.4, img_light_contrast: 0.8, img_components: 0.6}
  sources: [{title: "MedlinePlus – Tinea versicolor (ency)", url: null, retrieved: false}]

- slug: miliaria
  name_vi: "Rôm sảy"
  name_en: "Heat rash (miliaria)"
  summary_vi: "Nhiều chấm hoặc sẩn đỏ nhỏ li ti, có thể có bọng nước nhỏ trong, ngứa hoặc châm chích, xuất hiện khi nóng ẩm, ra nhiều mồ hôi, ở cổ, ngực, lưng, nếp gấp, nơi quần áo bó."
  summary_en: "Clusters of tiny red bumps, sometimes clear small blisters, itchy or prickly, appearing in hot humid weather with sweating, on neck, chest, back, skin folds and under tight clothing."
  body_sites: [trunk_front, back, neck, folds, face]
  weights: {papules: 0.9, itch: 0.8, burning: 0.5, redness: 0.5, blisters: 0.3, sweat_heat_trigger: 1, onset_lt3d: 0.6, onset_3_14d: 0.4, site_trunk_front: 0.7, site_back: 0.7, site_neck: 0.7, site_folds: 0.6, site_face: 0.3, img_components: 1, img_dispersion: 0.7}
  sources: [{title: "AAD – Heat rash (signs and symptoms)", url: null, retrieved: false}]

- slug: dyshidrotic_eczema
  name_vi: "Chàm tổ đỉa"
  name_en: "Dyshidrotic eczema (pompholyx)"
  summary_vi: "Mụn nước nhỏ sâu, ngứa nhiều ở cạnh ngón tay, lòng bàn tay, lòng bàn chân; sau đó khô, bong vảy, nứt; hay tái phát từng đợt."
  summary_en: "Deep-set small itchy blisters along the sides of fingers, palms and soles, later drying, peeling and cracking; relapses in episodes."
  body_sites: [hands, feet]
  weights: {blisters: 1, itch: 1, cracking: 0.3, scaling: 0.4, recurrent: 0.7, onset_3_14d: 0.5, site_hands: 1, site_feet: 0.8, img_components: 0.5}
  sources: [{title: "AAD – Dyshidrotic eczema (signs and symptoms)", url: null, retrieved: false}]
```

**Test sanity bắt buộc cho KB** (`ml/eval/eval_lookup.py`): với mỗi mục, vector dựng từ chính `weights` phải xếp trong top-5 và cosine với chính nó = 1. Cặp dễ nhầm cần ghi vào `KB_CARD.md` (ví dụ `tinea_ringworm`↔`contact_dermatitis`; `atopic_dermatitis`↔`dyshidrotic_eczema`; `folliculitis`↔`miliaria`↔`acne_vulgaris`; `vitiligo`↔`tinea_versicolor`): đây là lý do UI phải luôn nói "tương đồng, không phải chẩn đoán".

---

## PHỤ LỤC C — SAFETY RULES (nạp vào `app/agent/safety_rules.yaml`)

**Trạng thái:** bản soạn từ hướng dẫn công khai (AAD, Alberta Health, UCLA Health, Mayo Clinic…), **chưa được bác sĩ duyệt**. Quy tắc xác định, không dùng LLM, không nhìn ảnh; chỉ dùng câu trả lời mà người dùng tự khai (`facts`) và trạng thái hệ thống. Thông điệp trung tính: **không nêu tên bệnh, không mức nặng/nhẹ**. Cơ chế: đánh giá tất cả rule; hành động cao nhất thắng (`URGENT_MESSAGE` > `CLINICIAN_REVIEW` > `ROUTINE`); với `CLINICIAN_REVIEW` lấy `timeframe` gấp nhất (`same_day` > `soon` > `routine`); hiển thị tối đa 3 thông điệp, sắp theo mức độ. `URGENT_MESSAGE` dừng luồng: không lookup, không báo cáo tự động, chỉ hiện thông điệp + nút gọi 115 + nút tìm cơ sở y tế. Bộ đánh giá `when` do agent tự viết (cây `all/any/not`, **không dùng `eval`**).

Quy ước `facts`: bool từ form (mục 12) hoặc giá trị {none, some, many} cho triệu chứng (`some_or_more` = some|many); `image_status ∈ {PASS,RETAKE,REVIEW,ABSTAIN}`; `not_comparable_count` (số lần liên tiếp); `profile_type`.

```yaml
rules_version: "sr-2026.11-draft1"
status: PLACEHOLDER_NOT_CLINICIAN_REVIEWED
references:
  - {id: R1, title: "AAD – Rash 101 in adults: when to seek medical treatment", url: "https://www.aad.org/public/diseases/rashes"}
  - {id: R2, title: "AAD – Rash: when to seek medical treatment (breathing/swallowing/eye-lip swelling)", url: "https://www.aad.org/itchy-skin/rash-seek-medical-treatment"}
  - {id: R3, title: "AAD – Rashes (signs of infection)", url: "https://www.aad.org/dermatology-a-to-z/health-and-beauty/general-skin-care/rashes"}
  - {id: R4, title: "Alberta Health – Rash, age 12 and older", url: "https://myhealth.alberta.ca/Health/pages/conditions.aspx?hwid=rsh11"}
  - {id: R5, title: "UCLA Health – When to worry about a rash in adults", url: "https://www.uclahealth.org/news/article/red-and-itchy-when-worry-about-rash-adults"}
  - {id: R6, title: "AAD – Psoriasis: signs and symptoms (pustular/erythrodermic/arthritis)", url: "https://www.aad.org/public/diseases/psoriasis/what/symptoms"}
  - {id: R7, title: "AAD – Atopic dermatitis signs (eczema herpeticum)", url: "https://www.aad.org/dermatology-a-to-z/diseases-and-treatments/a---d/atopic-dermatitis/signs-symptoms"}
  - {id: R8, title: "Mayo Clinic – Ringworm (body): see doctor if no improvement in 2 weeks", url: "https://www.mayoclinic.org/diseases-conditions/ringworm-body/diagnosis-treatment/drc-20353782"}
  - {id: R9, title: "Doctor On Demand – When to go to urgent care for a rash (purple/black spots, mucous membranes, drug reaction)", url: "https://doctorondemand.com/blog/health/when-to-go-to-urgent-care-for-a-rash/"}
  - {id: R10, title: "Harvard Health – Ringworm (diabetes/weak immunity: check skin symptoms promptly)", url: "https://www.health.harvard.edu/a-to-z/ringworm-tinea-a-to-z"}

rules:
# ---------------- URGENT_MESSAGE ----------------
- id: U01
  action: URGENT_MESSAGE
  when: {all: [{fact: face_lip_swelling_or_breathing, eq: true}]}
  refs: [R2]
  message_vi: "Bạn có dấu hiệu cần được đánh giá y tế khẩn cấp (sưng mặt/môi, hoặc khó thở/khó nuốt). Hãy đến cơ sở y tế/cấp cứu gần nhất ngay hoặc gọi 115. Ứng dụng dừng phân tích tại đây."
  message_en: "You report signs that need urgent medical assessment (swelling of the face/lips, or trouble breathing/swallowing). Go to the nearest emergency facility now or call 115. The app stops its analysis here."
  reviewed_by_clinician: false

- id: U02
  action: URGENT_MESSAGE
  when: {all: [{fact: fever, eq: true}, {fact: spreading_rapidly, eq: true}]}
  refs: [R1, R5]
  message_vi: "Phát ban lan nhanh kèm sốt là dấu hiệu nên được đánh giá y tế ngay trong hôm nay. Hãy đến cơ sở y tế/cấp cứu hoặc gọi 115 nếu thấy mệt nhiều. Ứng dụng dừng phân tích tại đây."
  message_en: "A rapidly spreading rash with fever needs medical assessment today. Go to a medical facility/emergency department or call 115 if you feel very unwell. The app stops its analysis here."
  reviewed_by_clinician: false

- id: U03
  action: URGENT_MESSAGE
  when: {all: [{fact: blisters_mucosa, eq: true}]}
  refs: [R1, R4, R9]
  message_vi: "Phồng rộp hoặc loét quanh mắt, miệng hoặc vùng sinh dục cần được khám y tế ngay. Hãy đến cơ sở y tế/cấp cứu hoặc gọi 115. Ứng dụng dừng phân tích tại đây."
  message_en: "Blisters or sores around the eyes, mouth or genitals need medical assessment right away. Go to a medical facility/emergency department or call 115. The app stops its analysis here."
  reviewed_by_clinician: false

- id: U04
  action: URGENT_MESSAGE
  when: {all: [{fact: skin_peeling_or_raw_large, eq: true}]}
  refs: [R4, R6, R9]
  message_vi: "Da bong thành mảng lớn hoặc trầy xước, rỉ dịch trên diện rộng cần được khám y tế khẩn cấp. Hãy đến cơ sở y tế/cấp cứu hoặc gọi 115. Ứng dụng dừng phân tích tại đây."
  message_en: "Skin peeling in large areas or large raw, oozing areas needs urgent medical assessment. Go to a medical facility/emergency department or call 115. The app stops its analysis here."
  reviewed_by_clinician: false

- id: U05
  action: URGENT_MESSAGE
  when: {all: [{fact: purple_nonblanching_spots, eq: true}, {fact: fever, eq: true}]}
  refs: [R4, R9]
  message_vi: "Chấm hoặc vết tím/đen không mất đi khi ấn, kèm sốt, cần được khám y tế khẩn cấp. Hãy đến cơ sở y tế/cấp cứu hoặc gọi 115. Ứng dụng dừng phân tích tại đây."
  message_en: "Purple or dark spots that do not fade when pressed, together with fever, need urgent medical assessment. Go to a medical facility/emergency department or call 115. The app stops its analysis here."
  reviewed_by_clinician: false

- id: U06
  action: URGENT_MESSAGE
  when: {all: [{fact: severe_pain_hot_red_spreading, eq: true}]}
  refs: [R3, R5, R9]
  message_vi: "Vùng da đau dữ dội, đỏ nóng và lan rộng cần được khám y tế khẩn cấp. Hãy đến cơ sở y tế/cấp cứu hoặc gọi 115. Ứng dụng dừng phân tích tại đây."
  message_en: "Severe pain with hot, red, spreading skin needs urgent medical assessment. Go to a medical facility/emergency department or call 115. The app stops its analysis here."
  reviewed_by_clinician: false

- id: U07
  action: URGENT_MESSAGE
  when: {all: [{fact: known_eczema, eq: true}, {fact: blisters, in: [some, many]}, {fact: fever, eq: true}]}
  refs: [R7]
  message_vi: "Nếu bạn đang có chàm mà đột ngột nổi nhiều mụn nước đau kèm sốt, cần được khám y tế ngay trong hôm nay. Hãy đến cơ sở y tế/cấp cứu hoặc gọi 115. Ứng dụng dừng phân tích tại đây."
  message_en: "If you have eczema and suddenly develop many painful blisters with fever, you need medical assessment today. Go to a medical facility/emergency department or call 115. The app stops its analysis here."
  reviewed_by_clinician: false

- id: U08
  action: URGENT_MESSAGE
  when: {all: [{fact: known_psoriasis, eq: true}, {fact: fever, eq: true}, {any: [{fact: pustules, eq: many}, {fact: spreading_rapidly, eq: true}, {fact: skin_peeling_or_raw_large, eq: true}]}]}
  refs: [R6]
  message_vi: "Khi đang có vảy nến mà da đỏ lan rộng nhanh hoặc nổi nhiều mụn mủ kèm sốt, cần được khám y tế khẩn cấp. Hãy đến cơ sở y tế/cấp cứu hoặc gọi 115. Ứng dụng dừng phân tích tại đây."
  message_en: "If you have psoriasis and the skin turns red over large areas quickly or many pustules appear with fever, you need urgent medical assessment. Go to a medical facility/emergency department or call 115. The app stops its analysis here."
  reviewed_by_clinician: false

# ---------------- CLINICIAN_REVIEW: same_day ----------------
- id: C01
  action: CLINICIAN_REVIEW
  timeframe: same_day
  when: {all: [{fact: purple_nonblanching_spots, eq: true}]}
  refs: [R4, R9]
  message_vi: "Chấm hoặc vết tím/đen không mất khi ấn nên được bác sĩ đánh giá trong ngày. Hãy liên hệ cơ sở y tế sớm."
  message_en: "Purple or dark spots that do not fade when pressed should be assessed by a clinician the same day. Please contact a medical facility soon."
  reviewed_by_clinician: false

- id: C02
  action: CLINICIAN_REVIEW
  timeframe: same_day
  when: {all: [{fact: red_streak_from_lesion, eq: true}]}
  refs: [R3]
  message_vi: "Vệt đỏ lan ra từ vùng tổn thương là dấu hiệu nên được bác sĩ đánh giá trong ngày."
  message_en: "A red streak spreading from the lesion should be assessed by a clinician the same day."
  reviewed_by_clinician: false

- id: C03
  action: CLINICIAN_REVIEW
  timeframe: same_day
  when: {all: [{fact: new_medication_recent, eq: true}, {any: [{fact: spreading_rapidly, eq: true}, {fact: fever, eq: true}]}]}
  refs: [R9]
  message_vi: "Phát ban mới xuất hiện sau khi bắt đầu thuốc mới, lan nhanh hoặc kèm sốt, nên được bác sĩ đánh giá trong ngày. Đừng tự ngưng hay đổi thuốc khi chưa hỏi bác sĩ/dược sĩ."
  message_en: "A new rash after starting a new medicine that spreads quickly or comes with fever should be assessed the same day. Do not stop or change medicines before asking a doctor or pharmacist."
  reviewed_by_clinician: false

- id: C04
  action: CLINICIAN_REVIEW
  timeframe: same_day
  when: {all: [{fact: one_sided_band, in: [some, many]}, {fact: blisters, in: [some, many]}, {any: [{fact: pain, in: [some, many]}, {fact: burning, in: [some, many]}]}]}
  refs: [R1, R5]
  message_vi: "Dải mụn nước đau rát chỉ ở một bên cơ thể, nhất là gần mắt hoặc trên mặt, nên được bác sĩ đánh giá sớm trong ngày."
  message_en: "A painful, burning band of blisters on one side of the body, especially near the eye or on the face, should be assessed early the same day."
  reviewed_by_clinician: false

# ---------------- CLINICIAN_REVIEW: soon ----------------
- id: C05
  action: CLINICIAN_REVIEW
  timeframe: soon
  when: {all: [{fact: oozing, in: [some, many]}, {fact: crusting, in: [some, many]}, {fact: pain, in: [some, many]}]}
  refs: [R3, R5]
  message_vi: "Rỉ dịch, đóng mày kèm đau có thể là dấu hiệu da bị bội nhiễm. Nên để bác sĩ xem hồ sơ trong vài ngày tới."
  message_en: "Oozing, crusting and pain can be signs of an infected rash. A clinician should review the record within the next few days."
  reviewed_by_clinician: false

- id: C06
  action: CLINICIAN_REVIEW
  timeframe: soon
  when: {all: [{fact: lesion_changing_fast_or_ulcer, eq: true}]}
  refs: [R1]
  message_vi: "Tổn thương thay đổi nhanh, loét hoặc chảy máu nên được bác sĩ đánh giá sớm."
  message_en: "A lesion that changes quickly, ulcerates or bleeds should be assessed by a clinician soon."
  reviewed_by_clinician: false

- id: C07
  action: CLINICIAN_REVIEW
  timeframe: soon
  when: {all: [{fact: known_psoriasis, eq: true}, {fact: joint_pain_or_stiffness, eq: true}]}
  refs: [R6]
  message_vi: "Đau hoặc cứng khớp khi đang có vảy nến nên được bác sĩ đánh giá sớm."
  message_en: "Joint pain or stiffness in someone with psoriasis should be assessed by a clinician soon."
  reviewed_by_clinician: false

- id: C08
  action: CLINICIAN_REVIEW
  timeframe: soon
  when: {all: [{fact: immune_or_diabetes, eq: true}]}
  refs: [R4, R10]
  message_vi: "Vì bạn có suy giảm miễn dịch hoặc đái tháo đường, nên để bác sĩ xem các triệu chứng da mới sớm hơn bình thường."
  message_en: "Because you have a weakened immune system or diabetes, new skin symptoms should be reviewed by a clinician sooner than usual."
  reviewed_by_clinician: false

- id: C09
  action: CLINICIAN_REVIEW
  timeframe: soon
  when: {all: [{fact: night_itch_contacts, in: [some, many]}]}
  refs: [R1]
  message_vi: "Ngứa nhiều về đêm kèm người sống cùng cũng ngứa nên được bác sĩ đánh giá sớm vì có thể lây cho người xung quanh."
  message_en: "Intense night-time itch with others in the household also itching should be assessed soon because it can spread to people around you."
  reviewed_by_clinician: false

# ---------------- CLINICIAN_REVIEW: routine ----------------
- id: C10
  action: CLINICIAN_REVIEW
  timeframe: routine
  when: {all: [{fact: rash_lasting_over_2_weeks, eq: true}]}
  refs: [R8]
  message_vi: "Tình trạng kéo dài hơn 2 tuần mà chưa cải thiện nên được bác sĩ da liễu đánh giá."
  message_en: "A skin problem that has lasted more than 2 weeks without improving should be assessed by a dermatologist."
  reviewed_by_clinician: false

- id: C11
  action: CLINICIAN_REVIEW
  timeframe: routine
  when: {any: [{fact: image_status, in: [REVIEW, ABSTAIN]}]}
  refs: []
  message_vi: "Hệ thống chưa đủ dữ liệu từ ảnh để phân tích chắc chắn. Bạn có thể chụp lại theo hướng dẫn hoặc nhờ bác sĩ xem hồ sơ."
  message_en: "The app does not have enough reliable image data to analyse. You can retake the photo following the guide or ask a clinician to review the record."
  reviewed_by_clinician: false

- id: C12
  action: CLINICIAN_REVIEW
  timeframe: routine
  when: {all: [{fact: not_comparable_count, gte: 3}]}
  refs: []
  message_vi: "Nhiều lần chụp liên tiếp không so sánh được với nhau. Nên chụp lại đúng khung hướng dẫn hoặc nhờ bác sĩ xem."
  message_en: "Several consecutive photos could not be compared. Retake photos using the same guide frame or ask a clinician to review."
  reviewed_by_clinician: false

- id: C13
  action: CLINICIAN_REVIEW
  timeframe: routine
  when: {all: [{fact: profile_type, eq: other}]}
  refs: []
  message_vi: "Hồ sơ 'tình trạng chưa rõ' luôn nên được bác sĩ xem để xác định hướng theo dõi."
  message_en: "A record for an unclear skin problem should always be reviewed by a clinician to decide how to follow it."
  reviewed_by_clinician: false

default_action: ROUTINE
```

**Test bắt buộc:** mỗi rule có ≥ 1 test kích hoạt và ≥ 1 test không kích hoạt; xung đột nhiều rule → hành động cao nhất thắng; mọi `message_*` không chứa tên tình trạng trong KB, không chứa `%`, "nặng/nhẹ/nguy hiểm/khỏi", không khuyên dùng/ngưng thuốc (ngoại lệ có chủ đích: C03 nhắc "đừng tự ngưng hay đổi thuốc khi chưa hỏi bác sĩ/dược sĩ" — đây là lời nhắc an toàn, được whitelist theo `id`).

---

## PHỤ LỤC D — DANH BẠ CƠ SỞ KHÁM DA LIỄU THẬT (nạp vào `app/data/clinics_directory.yaml`)

**Trạng thái:** thu thập ngày **21/11/2026** từ các trang công khai (URL ghi từng mục). Đây là danh bạ **thông tin công khai**, không phải đối tác của DermaCare: `listing_type: directory`, không Partner, không nhận consent, không nút gửi hồ sơ. Thông tin có thể thay đổi (nhất là tên phường sau sắp xếp lại đơn vị hành chính, giờ làm việc, số điện thoại) → con người phải gọi/xem website chính thức xác nhận (HUMAN_TODO #13). Các nguồn là trang đặt khám/tin y tế, không phải nguồn chính thức của cơ sở. **Toạ độ để `null`**, chạy `scripts/geocode_clinics.py` rồi kiểm tra tay trên bản đồ; agent không tự điền toạ độ từ trí nhớ.

```yaml
directory_version: "dir-2026.11.21"
checked_at: "2026-11-21"
city: "TP. Hồ Chí Minh"
clinics:

- slug: bvdl-tphcm
  name: "Bệnh viện Da liễu TP.HCM"
  type: "Bệnh viện chuyên khoa da liễu hạng I (công lập, trực thuộc Sở Y tế TP.HCM)"
  address_text: "2 Nguyễn Thông, phường Xuân Hòa, TP.HCM"
  address_note: "Địa chỉ cũ: 2 Nguyễn Thông, phường Võ Thị Sáu (Phường 6), Quận 3"
  district: "Quận 3 (cũ)"
  phone: "(028) 3930 8131"
  hours_note: "Theo trang đặt khám: T2–T6 7h–11h & 13h–16h; T7 7h30–11h & 13h–18h30; CN 7h30–11h & 13h–15h (khám dịch vụ/ngoài giờ). BHYT chỉ giờ hành chính T2–T6. Cần xác nhận lại."
  lat: null
  lng: null
  geocode_status: pending
  listing_type: directory
  sources:
    - {title: "Pharmacity – Thăm khám tại BV Da liễu TP.HCM (địa chỉ, SĐT)", url: "https://www.pharmacity.vn/tham-kham-tai-benh-vien-da-lieu-tp-ho-chi-minh.htm", retrieved: true}
    - {title: "Medpro – BV Da liễu TP.HCM (địa chỉ, khoa)", url: "https://medpro.vn/dalieuhcm", retrieved: true}
    - {title: "Medpro – Hướng dẫn đi khám (lịch làm việc)", url: "https://medpro.vn/tin-tuc/huong-dan-di-kham-benh-vien-da-lieu-tphcm", retrieved: true}

- slug: bvdhyd-da-lieu-hong-bang
  name: "Khoa Da liễu – Thẩm mỹ da, Bệnh viện Đại học Y Dược TP.HCM (cơ sở 215 Hồng Bàng)"
  type: "Khoa da liễu của bệnh viện đại học (công lập)"
  address_text: "215 Hồng Bàng, TP.HCM (lầu 1, phòng 17–20)"
  address_note: "Nguồn ghi: phường 11, quận 5 (tên cũ); tên phường hiện hành cần xác nhận"
  district: "Quận 5 (cũ)"
  phone: null
  hours_note: "Cần xác nhận trên website bệnh viện. Một nguồn ghi phí khám ban đầu da liễu 150.000đ (có thể đã đổi)."
  lat: null
  lng: null
  geocode_status: pending
  listing_type: directory
  sources:
    - {title: "Medpro – Khoa Da liễu BV Đại học Y Dược TP.HCM", url: "https://medpro.vn/tin-tuc/khoa-da-lieu-bv-dai-hoc-y-duoc-tphcm", retrieved: true}

- slug: bv-fv
  name: "Bệnh viện FV (khám da liễu – cần xác nhận khoa)"
  type: "Bệnh viện đa khoa tư nhân"
  address_text: "6 Nguyễn Lương Bằng, phường Tân Mỹ, TP.HCM"
  address_note: "Khu Phú Mỹ Hưng, Quận 7 (cũ)"
  district: "Quận 7 (cũ)"
  phone: null
  hours_note: "Nguồn ghi: T2–T6 8h–17h; T7 8h–12h. Cần xác nhận có khám da liễu/chàm và giờ hiện hành."
  lat: null
  lng: null
  geocode_status: pending
  listing_type: directory
  sources:
    - {title: "Medpro – Chữa chàm da ở đâu (nhắc BV FV)", url: "https://medpro.vn/tin-tuc/chua-cham-da-o-dau", retrieved: true}

- slug: pk-pensilia
  name: "Phòng khám Da liễu – Thẩm mỹ Pensilia"
  type: "Phòng khám tư nhân (da liễu – thẩm mỹ)"
  address_text: "411/2 – 413 – 415 Nguyễn Đình Chiểu, TP.HCM"
  address_note: "Nguồn ghi: phường 5, Quận 3 (tên cũ)"
  district: "Quận 3 (cũ)"
  phone: null
  hours_note: "Chưa có thông tin; gọi xác nhận."
  lat: null
  lng: null
  geocode_status: pending
  listing_type: directory
  sources:
    - {title: "Hello Bacsi – danh sách cơ sở (Pensilia)", url: "https://hellobacsi.com/care/benh-vien/benh-vien-da-lieu-tpho-chi-minh-1581", retrieved: true}

- slug: pk-tao-do-q10
  name: "Phòng khám Táo Đỏ – cơ sở Quận 10"
  type: "Phòng khám tư nhân (da liễu)"
  address_text: "35A1 đường 3/2, TP.HCM"
  address_note: "Nguồn ghi: Phường 11, Quận 10 (tên cũ). Nguồn là bài tổng hợp, độ tin cậy thấp hơn — ưu tiên xác minh."
  district: "Quận 10 (cũ)"
  phone: null
  hours_note: "Chưa có thông tin; gọi xác nhận."
  lat: null
  lng: null
  geocode_status: pending
  listing_type: directory
  sources:
    - {title: "Hello Bacsi – Top 5 phòng khám da liễu TP.HCM", url: "https://hellobacsi.com/suc-khoe/benh-vien/top-5-phong-kham-da-lieu-uy-tin-chat-luong-tai-tp-hcm/", retrieved: true}

- slug: pk-tao-do-q5
  name: "Phòng khám Táo Đỏ – cơ sở Quận 5"
  type: "Phòng khám tư nhân (da liễu)"
  address_text: "471 Nguyễn Chí Thanh, TP.HCM"
  address_note: "Nguồn ghi: Phường 15, Quận 5 (tên cũ). Nguồn là bài tổng hợp, độ tin cậy thấp hơn — ưu tiên xác minh."
  district: "Quận 5 (cũ)"
  phone: null
  hours_note: "Chưa có thông tin; gọi xác nhận."
  lat: null
  lng: null
  geocode_status: pending
  listing_type: directory
  sources:
    - {title: "Hello Bacsi – Top 5 phòng khám da liễu TP.HCM", url: "https://hellobacsi.com/suc-khoe/benh-vien/top-5-phong-kham-da-lieu-uy-tin-chat-luong-tai-tp-hcm/", retrieved: true}
```

**Việc cho agent:** (1) nạp YAML vào bảng `clinics` (`is_synthetic=false`, `verification_status='verified'` chỉ có nghĩa "danh bạ đã kiểm tra nguồn", **không** cho phép nhận consent); (2) viết `geocode_clinics.py` như mục 11.1; (3) UI hiển thị nhãn "Thông tin công khai, chưa hợp tác với DermaCare — vui lòng gọi xác nhận"; (4) thêm test mục 18(d). Mở rộng danh bạ (Hà Nội, Đà Nẵng, tỉnh khác, cơ sở bác sĩ chuyên khoa) là việc của con người.

---

## PHỤ LỤC E — NGUỒN THAM KHẢO DÙNG KHI SOẠN PHỤ LỤC B/C/D

| Nhóm | Nguồn (đã đọc khi soạn) |
|------|-------------------------|
| Red flag phát ban | AAD – Rash 101 in adults (aad.org/public/diseases/rashes; aad.org/itchy-skin/rash-seek-medical-treatment; aad.org/dermatology-a-to-z/health-and-beauty/general-skin-care/rashes); Alberta Health myhealth.alberta.ca (rash 12+); UCLA Health "When to worry about a rash"; Doctor On Demand "When to go to urgent care for a rash" |
| Viêm da cơ địa | AAD (atopic dermatitis signs & symptoms, kể cả eczema herpeticum); NIAMS/NIH; MedlinePlus 000853 |
| Vảy nến | AAD (symptoms, overview); MedlinePlus 000434; National Psoriasis Foundation (plaque) |
| Nấm da | CDC ringworm symptoms; AAD ringworm symptoms; MedlinePlus 000877; Harvard Health; Mayo Clinic |
| Chốc | AAD impetigo symptoms; CDC About impetigo; Harvard Health |
| Cơ sở y tế TP.HCM | Pharmacity, Medpro, Hello Bacsi (trang đặt khám/tin y tế; không phải nguồn chính thức của cơ sở) |
| Các mục KB `retrieved:false` | Chưa đọc trang cụ thể khi soạn; bác sĩ/agent phải đối chiếu AAD/CDC/NHS/MedlinePlus trước khi dùng thật |
