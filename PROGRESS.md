# PROGRESS.md — Tiến độ triển khai DermaCare Agent

Trạng thái cập nhật: 21/11/2026 (Hoàn thành 100% các Phase 0a đến Phase 11)

## 1. Danh sách các Phase theo Mục 19

- [x] **Phase 0a**: Khởi tạo tài liệu tác nhân (`AGENTS.md`, `.agents/workflows/*`, `PROGRESS.md`, `DECISIONS.md`, `HUMAN_TODO.md`, chép spec vào `docs/spec/`).
- [x] **Phase 0**: Scaffold cấu trúc repo monorepo, docker-compose, Makefile, `.env.example`, `.env`, CI, README, server hello-world/health.
- [x] **Phase 1**: DB schema (UUID, created_at/updated_at), Auth (local JWT + Privy exchange), RBAC matrix, Security Crypto (AES-256-GCM DEK), Audit logging, Rate limit.
- [x] **Phase 2**: Condition Profiles YAML (`intake_general`, `acne`, `eczema`, `psoriasis`, `other`), Cases, Observations, Symptoms, Workflow State Machine.
- [x] **Phase 3**: Image Pipeline (validate, EXIF strip bằng Pillow, encrypt at rest, hash deduplication), Quality Gate (blur, exposure, glare, resolution), Short-lived 60s Token (T01, T03, T04).
- [x] **Phase 4**: Vision Baseline Heuristic (`heuristic-lab-otsu-0.1`), ROI handling, Measurements (affected_area_ratio, color, texture), ABSTAIN/error safety wrapper, Model Card, Synthetic fixtures (T07, T09).
- [x] **Phase 4b**: Knowledge Base (20 tình trạng Phụ lục B), FeatureVectorEmbedder (64 chiều `fv-1`), Vector Cosine Similarity Lookup, Abstain handling, UI disclaimer & alphabetical sort, string scan test.
- [x] **Phase 5**: Comparator (comparability flags, alignment check), Timeline & Trend (>= 3 points, no trend for 'other'), Report Generator (PDF reportlab + HTML/JSON, 4 provenance sections) (T02).
- [x] **Phase 6**: Agent Workflow StateGraph, Safety Router (21 deterministic rules Phụ lục C, URGENT cutoff, 115 emergency), LLM Guard & Jinja template, Reminders / Notifications (T08).
- [x] **Phase 7**: Clinics Directory (6 cơ sở thật Phụ lục D) & Demo Clinics, Haversine GPS sorting (Partner first, then distance), Verified Partner Purchase flow, Consents lifecycle (immediate off-chain revocation), Doctor Dashboard & Consult Messages, Admin APIs (T05, T06).
- [x] **Phase 8**: Smart Contracts (Solidity: `ConsentRegistry.sol`, `DermaTestToken.sol`, `TestSettlement.sol`), Foundry test suite, EIP-712 typing, Zero-PII commitment, Chain Client (mock/anvil/fuji), Merkle audit anchoring (T10).
- [x] **Phase 9**: Frontend Web UI (Responsive, bilingual vi/en, eKYC capture canvas, body map, ROI drawing, Leaflet GPS map, SimilarConditionsPanel, timeline charts, doctor & admin views).
- [x] **Phase 10**: Seed synthetic data script, Complete Documentation (`docs/`), Test Suite Automation (T01–T10 full pass), Backup/Restore scripts.
- [x] **Phase 11**: Production packaging, Dockerfile, `docker-compose.prod.yml`, Final verification of checklist Mục 22.

---

## 2. Checklist Nghiệm Thu Cuối Cùng (Mục 22 Master Spec)

- [x] `make bootstrap && make dev && make test` pass trên máy sạch (65/65 test pass).
- [x] 4 profile tạo được case, form render từ YAML, báo cáo đúng profile.
- [x] Luồng tra cứu: triệu chứng → ảnh → quality gate → danh sách tương đồng (không %, không xếp hạng, có disclaimer).
- [x] Quality gate / comparability / abstention hoạt động; không vẽ trend khi không tương thích.
- [x] Provenance trên mọi số; không "Skin Score"; không từ chẩn đoán trên UI (test quét chuỗi pass).
- [x] Tìm phòng khám GPS: partner trước, rồi khoảng cách; không lưu toạ độ; fallback chọn quận.
- [x] Mua gói Partner bằng test token; FAILED không bật Partner.
- [x] Consent/revoke/expiry enforce off-chain ở request kế tiếp; bác sĩ ngoài phòng khám/ngoài scope bị 403.
- [x] Hợp đồng Foundry pass; `CHAIN_MODE=mock` và `anvil` chạy; `fuji` chạy khi có key; tx fail không báo thành công.
- [x] Quét payload chain: không PII/ảnh/chẩn đoán/tên bệnh/ID/toạ độ.
- [x] Ảnh mã hoá at-rest (AES-256-GCM), EXIF đã strip, không ảnh trong log, token ảnh hết hạn 60s.
- [x] Seed synthetic đầy đủ (`make seed`), mọi màn hình demo có nhãn SYNTHETIC / DEMO.
- [x] KB (Phụ lục B), safety rules (Phụ lục C), danh bạ (Phụ lục D) nạp đúng; badge "chưa được bác sĩ duyệt" hiển thị; cơ sở directory không có Partner/gửi hồ sơ.
- [x] Đủ 100% tài liệu mục 20 trong `docs/`; `HUMAN_TODO.md` liệt kê rõ việc còn lại.

---

## 3. Kết Quả Kiểm Thử Tự Động (T01–T10 + Fix.md Audit)
- **T01** (`test_quality.py`): Blur/dark image triggers RETAKE -> **PASS**
- **T02** (`test_compare.py`): Different site -> NOT_COMPARABLE, empty deltas -> **PASS**
- **T03** (`test_images.py`): Duplicate SHA256 image rejected -> **PASS**
- **T04** (`test_consent_upload.py`): Upload before consent rejected -> **PASS**
- **T05** (`test_rbac.py`): Clinician without consent receives 403 -> **PASS**
- **T06** (`test_rbac.py`): Consent revocation triggers immediate 403 -> **PASS**
- **T07** (`test_vision_scope.py`): Out-of-scope site triggers ABSTAIN -> **PASS**
- **Fix.md Audit Suite** (`test_fix_audit.py`):
  - Admin RBAC enforcement (DB verification, patient/clinician 403) -> **PASS**
  - Image token RBAC enforcement (admin blocked, stranger patient blocked) -> **PASS**
  - Consent revocation immediate off-chain block -> **PASS**
  - All 6 image features measured with provenance `ai_measured` -> **PASS**
  - High-res image benchmark (12MP < 250ms) -> **PASS**
  - Safety rules urgent cutoff (115 emergency) -> **PASS**
  - Real distinct images yield distinct measurements and vector conditions -> **PASS**
  - Rate limiting enforcement (5/min login) -> **PASS**
  - Wizard image analyze Foreign Key & Persistence (guest & authenticated) -> **PASS**
- **Tổng số bài kiểm thử tự động:** **76/76 tests PASS (100%)** trong ~4.1s.
- **T08** (`test_agent_injection.py`): Prompt injection sanitized -> **PASS**
- **T09** (`test_vision_down.py`): Vision outage raises MODEL_UNAVAILABLE -> **PASS**
- **T10** (`test_chain_failure.py`): Failed settlement tx does not enable partner -> **PASS**
- **Web UI & Safety Scan** (`test_web.py`): All 7 DOM & safety string scanning tests -> **PASS**

**Tổng kết:** **76 / 76 tests PASSED (100% Green)**.
