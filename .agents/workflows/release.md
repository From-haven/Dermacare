# Workflow: Release & Checklist Nghiệm Thu

## 1. Checklist Nghiệm Thu Cuối (Mục 22 Master Spec)
- [ ] `make bootstrap && make dev && make test` pass trên môi trường.
- [ ] 4 profile tạo được case, form render từ YAML, báo cáo đúng profile.
- [ ] Luồng tra cứu: triệu chứng → ảnh → quality gate → danh sách tương đồng (không %, không xếp hạng, có disclaimer).
- [ ] Quality gate / comparability / abstention hoạt động; không vẽ trend khi không tương thích.
- [ ] Provenance trên mọi số; không "Skin Score"; không từ chẩn đoán trên UI (test quét chuỗi).
- [ ] Tìm phòng khám GPS: partner trước, rồi khoảng cách; không lưu toạ độ; fallback chọn quận.
- [ ] Mua gói Partner bằng test token; FAILED không bật Partner.
- [ ] Consent/revoke/expiry enforce off-chain ở request kế tiếp; bác sĩ ngoài phòng khám/ngoài scope bị 403.
- [ ] Contract test pass; `CHAIN_MODE=mock` và `fuji` chạy khi có key; tx fail không báo thành công.
- [ ] Quét payload chain: không PII/ảnh/chẩn đoán/tên bệnh/ID/toạ độ.
- [ ] Ảnh mã hoá at-rest, EXIF đã strip, không ảnh trong log, token ảnh hết hạn 60s.
- [ ] Seed synthetic đầy đủ, mọi màn hình demo có nhãn SYNTHETIC / DEMO.
- [ ] KB (Phụ lục B), safety rules (Phụ lục C), danh bạ (Phụ lục D) nạp đúng; badge "chưa được bác sĩ duyệt" hiển thị; cơ sở directory không có Partner/gửi hồ sơ.
- [ ] Đủ tài liệu Mục 20; `HUMAN_TODO.md` liệt kê rõ việc còn lại.

## 2. Bằng chứng P1–P10 (Mục 25 Master Spec)
- P1: Product Walkthrough (`docs/DEMO_SCRIPT.md`)
- P2: Deployed Product (`docs/DEPLOY.md`, guides, `docs/RELEASE_NOTES.md`)
- P3: Source Code (README, ARCHITECTURE, migrations, OPENAPI)
- P4: Dataset Register (`ml/DATASET_REGISTER.md`)
- P5: Model Card (`ml/MODEL_CARD.md`, `ml/eval/*`)
- P6: Longitudinal Evidence (`docs/PILOT_PROTOCOL.md`)
- P7: Agent Trace (`docs/ADMIN_GUIDE.md`, audit log scrubber)
- P8: Blockchain Evidence (`docs/BLOCKCHAIN_EVIDENCE.md`)
- P9: Security & Privacy (`docs/SECURITY_PRIVACY.md`)
- P10: QA & Release Checklist (`docs/TEST_REPORT.md`, `docs/RELEASE_CHECKLIST.md`)
