# AGENTS.md — Hướng dẫn làm việc cho Coding Agent

## 1. Tóm tắt sản phẩm
DermaCare Agent là web app y tế hỗ trợ:
1. Khai báo vùng da (body map) & triệu chứng trực quan;
2. Chụp ảnh eKYC chuẩn khung với Quality Gate tự động;
3. Đo chỉ số lặp lại (heuristic) & tra cứu tình trạng tương đồng từ Vector DB (64 chiều, chỉ tham khảo, KHÔNG chẩn đoán, KHÔNG %, KHÔNG xếp hạng);
4. Tìm phòng khám da liễu gần nhất qua GPS (ưu tiên Verified Partner);
5. Cấp / thu hồi quyền xem hồ sơ có bằng chứng Avalanche (commitment ngẫu nhiên, không PII);
6. Theo dõi tiến triển (Timeline) & xuất báo cáo PDF cho bác sĩ.

## 2. Quy tắc cốt lõi (Mục 0 Master Spec)
1. **Tự quyết:** Chọn phương án mặc định, ghi vào `DECISIONS.md`. Không hỏi lại nếu tài liệu đã có hướng dẫn.
2. **Tuân thủ Phase (Mục 19):** Code → Chạy test gate → Ghi kết quả → Cập nhật `PROGRESS.md`. Không nhảy cóc khi gate chưa pass.
3. **Việc con người:** KHÔNG bịa. Ghi rõ vào `HUMAN_TODO.md` và dùng cơ chế fallback (mock / stub / ABSTAIN / synthetic).
4. **CẤM TUYỆT ĐỐI:**
   - Commit secret, API key hoặc ảnh bệnh nhân thật.
   - Ghi PII, ảnh, triệu chứng, chẩn đoán, tên bệnh lên blockchain.
   - Log ảnh, nội dung triệu chứng, tin nhắn tư vấn hoặc toạ độ GPS chính xác.
   - Để LLM tự chẩn đoán hoặc tự sinh danh sách bệnh.
   - Hiển thị % mắc bệnh, điểm "Skin Score", mức nặng/nhẹ, hoặc mức độ cần khám suy từ ảnh.
   - Lưu toạ độ GPS chính xác vào database.
5. **Dữ liệu & Provenance:** Mọi số liệu hiển thị phải có `provenance ∈ {ai_measured, user_reported, clinician_entered, synthetic}`. Dữ liệu demo phải gắn nhãn SYNTHETIC / DEMO.
6. **Độ tin cậy:** Báo "xong" phải kèm output test thật, danh sách file và việc chưa làm. Không tắt test cho xanh.

## 3. Lệnh vận hành chính (Makefile)
- `make bootstrap`: Kiểm tra môi trường, cài đặt dependency và chuẩn bị database.
- `make dev`: Chạy đồng thời API server, worker và Web UI.
- `make test`: Chạy toàn bộ test suite (API, vision, contracts, web, T01–T10).
- `make test-api`: Chạy test API và RBAC.
- `make seed`: Nạp dữ liệu synthetic, danh bạ phòng khám và cơ sở kiến thức KB.
- `make openapi`: Xuất tài liệu OpenAPI JSON.
- `make reset`: Đặt lại DB và xoá cache.

## 4. Đường dẫn tài liệu quan trọng
- Master Specification: `docs/spec/MASTER_SPEC.md`
- Tài liệu thiết kế đồ án gốc: `docs/spec/DermaCare_Agent.docx`
- Theo dõi tiến độ: `PROGRESS.md`
- Nhật ký quyết định kỹ thuật: `DECISIONS.md`
- Danh sách việc cần con người: `HUMAN_TODO.md`
- Workflows: `.agents/workflows/` (`resume.md`, `phase-next.md`, `gate-check.md`, `release.md`)
