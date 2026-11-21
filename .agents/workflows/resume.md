# Workflow: Resume (Khôi phục ngữ cảnh làm việc)

Khi bắt đầu phiên làm việc mới hoặc tiếp tục dự án:

1. **Đọc tài liệu trạng thái:**
   - Đọc `PROGRESS.md` để xác định phase hiện tại đang làm dở hoặc phase kế tiếp.
   - Đọc `DECISIONS.md` để nắm các quyết định kiến trúc đã chốt.
   - Đọc `HUMAN_TODO.md` để biết các ranh giới fallback đang áp dụng.

2. **Chạy kiểm tra Gate gần nhất:**
   - Chạy lệnh test tương ứng của phase gần nhất để đảm bảo không có hồi quy:
     ```bash
     python3 -m unittest discover -s tests -p "test_*.py"
     ```

3. **Báo cáo trạng thái ngắn gọn:**
   - Phase hiện tại.
   - Trạng thái các bài test T01–T10.
   - Hành động tiếp theo cần thực hiện theo Mục 19 Master Spec.
