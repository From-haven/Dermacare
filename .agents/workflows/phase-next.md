# Workflow: Phase Next (Chuyển sang Phase kế tiếp)

1. **Điều kiện tiên quyết:**
   - Toàn bộ gate tests của phase hiện tại đã PASS 100%.
   - Không có test bị bỏ qua hoặc can thiệp sai lệch.

2. **Các bước thực hiện:**
   - Tra cứu phạm vi công việc của phase mới trong Mục 19 `docs/spec/MASTER_SPEC.md`.
   - Lập danh sách các file cần tạo/chỉnh sửa (models, schemas, services, routers, tests).
   - Viết code và viết test tự động đi kèm.
   - Chạy test kiểm thử gate của phase:
     ```bash
     python3 -m unittest discover -s tests -p "test_*.py"
     ```
   - Cập nhật mục tick `[x]` trong `PROGRESS.md`.
   - Nếu có quyết định kỹ thuật mới, ghi vào `DECISIONS.md`.
   - Nếu phát sinh việc cần con người, ghi vào `HUMAN_TODO.md`.
