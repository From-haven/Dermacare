# Workflow: Gate Check (Kiểm tra cổng nghiệm thu)

Quy trình xác minh nghiệm thu từng phase theo Mục 19 `docs/spec/MASTER_SPEC.md`:

| Phase | Tên cổng | Lệnh kiểm tra bắt buộc |
|---|---|---|
| 0a | Files & Docs Setup | Kiểm tra tồn tại `AGENTS.md`, workflows, `docs/spec/MASTER_SPEC.md` |
| 0 | Scaffold & Health | Khởi động server và gọi `/health` |
| 1 | DB, Auth, RBAC | Test auth, token JWT, password hash, RBAC matrix |
| 2 | Profiles & Cases | Validate YAML profiles, transition state machine |
| 3 | Image & Quality | Test T01 (mờ/tối), T03 (duplicate), T04 (consent upload), token 60s |
| 4 | Vision Baseline | Test T07 (out of scope abstain), T09 (vision down), measure |
| 4b | Knowledge Base | Test cosine lookup, top-K match, schema validation, quét từ cấm |
| 5 | Comparator & Report | Test T02 (khác vùng -> NOT_COMPARABLE), deltas, report PDF/HTML |
| 6 | Agent & Safety | Test T08 (prompt injection), 21 safety rules |
| 7 | Clinics & Consent | Test T05 (403 không consent), T06 (revoke tức thì), haversine GPS, partner |
| 8 | Chain & Contracts | Test T10 (tx fail không bật partner), EIP-712, no PII on chain |
| 9 | Frontend UI | Kiểm tra UI routes, eKYC capture, Leaflet map, quét ký tự `%` |
| 10 | Seed & Verification | Nạp seed synthetic, chạy toàn bộ test suite T01–T10 |
| 11 | Production Package | Kiểm tra Dockerfile, compose prod, tài liệu vận hành |
