# HUMAN_TODO.md — Danh sách các việc cần con người thực hiện

> Theo quy tắc Mục 0.3 và Mục 21 của Master Spec: Agent **KHÔNG ĐƯỢC TỰ BỊA** các thông tin dưới đây. Mọi tính năng tương ứng đã được thiết kế sẵn cơ chế fallback (mock, stub, ABSTAIN, synthetic) để hệ thống hoạt động hoàn chỉnh.

---

| # | Hạng mục | Chi tiết cần con người xử lý | Trạng thái hiện tại |
|---|---|---|---|
| 1 | **Privy App ID & Secret** | Đăng ký tài khoản tại [privy.io](https://privy.io), tạo App mới, cấu hình Google Login, bật Embedded Wallet và điền `PRIVY_APP_ID`, `PRIVY_APP_SECRET`, `NEXT_PUBLIC_PRIVY_APP_ID` vào `.env`. | Đang dùng fallback `AUTH_MODE=local`, `WALLET_MODE=local-dev` |
| 2 | **Ví Relayer & AVAX Faucet** | Tạo ví Avalanche testnet riêng cho relayer, lấy AVAX Fuji từ faucet chính thức của Avalanche Builder Hub và điền `RELAYER_PRIVATE_KEY` vào `.env`. Tuyệt đối không dùng ví có tiền thật. | Đang dùng fallback `CHAIN_MODE=mock` |
| 3 | **LLM API Key (Tuỳ chọn)** | Nếu muốn sử dụng LLM để diễn đạt tóm tắt báo cáo thay cho Jinja template mặc định, cung cấp `LLM_API_KEY` (Gemini, OpenAI hoặc Anthropic) và đặt `LLM_PROVIDER`. | Đang dùng fallback `LLM_PROVIDER=none` (Jinja template chuẩn) |
| 4 | **Bác sĩ da liễu thẩm định KB** | Mời bác sĩ da liễu có chứng chỉ hành nghề xem xét, chuẩn hóa nội dung mô tả và trọng số trong `app/knowledge/conditions.yaml` (Phụ lục B). Chạy `scripts/kb_review.py` để cập nhật `reviewed_by_clinician: true`. | Hiện giữ `reviewed_by_clinician: false` kèm badge cảnh báo |
| 5 | **Bác sĩ thẩm định Safety Rules** | Bác sĩ chuyên khoa duyệt 21 quy tắc cảnh báo an toàn trong `app/agent/safety_rules.yaml` (Phụ lục C) trước khi áp dụng cho người bệnh thực tế. | Hiện giữ `reviewed_by_clinician: false` |
| 6 | **Xác minh danh bạ cơ sở khám** | Gọi điện thoại hoặc truy cập cổng thông tin chính thức của các cơ sở y tế ở Phụ lục D để xác nhận lại địa chỉ, giờ khám, dịch vụ da liễu. Chạy `scripts/geocode_clinics.py` và kiểm tra toạ độ thủ công. | `geocode_status: pending`, `listing_type: directory` |
| 7 | **Hiệu chỉnh ngưỡng Quality Gate** | Thu thập bộ ảnh thực tế gán nhãn `acceptable/` và `retake/`, chạy `ml/eval/calibrate_quality.py` để tính toán bộ ngưỡng tối ưu. | Đang dùng ngưỡng uncalibrated mặc định trong `thresholds.yaml` |
| 8 | **Rà soát pháp lý y tế** | Tham vấn luật sư y tế về Luật BVDLCN 91/2025/QH15, Nghị định 356/2025/NĐ-CP và quy định quảng cáo dịch vụ khám chữa bệnh cho nhãn "Verified Partner". | Đã ghi rõ điều khoản giới hạn trách nhiệm tại `/about-limits` |
| 9 | **Bản quyền thang đo POEM** | Xác nhận bản quyền sử dụng thang đo POEM (Patient-Oriented Eczema Measure) trước khi bật cờ `poem_enabled=true`. | Mặc định `poem_enabled=false` |
| 10 | **Hạ tầng Production** | Cung cấp tài khoản Vercel/Render/Fly, PostgreSQL có extension pgvector, Redis và Cloudflare R2 / AWS S3 bucket riêng tư khi đưa lên production. | Đang dùng cấu hình local / Docker |
