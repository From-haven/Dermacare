# Model Card: Heuristic LAB-Otsu Vision Baseline (heuristic-lab-otsu-0.1)

## Model Details
- **Tên:** `heuristic-lab-otsu-0.1`
- **Phiên bản:** `0.1.0`
- **Loại hình:** Thuật toán phân đoạn kinh nghiệm (Heuristic Rule-based Computer Vision), không sử dụng trọng số mạng nơ-ron học sâu (Deep Learning).
- **Nhãn hiển thị:** "heuristic, không phải thang lâm sàng".

## Mục đích sử dụng
- Tính toán chỉ số diện tích bất thường màu sắc (`affected_area_ratio`) và độ tương phản màu đỏ trên vùng quan tâm (ROI).
- Tạo các đặc trưng hình ảnh cho vector truy vấn tương đồng 64 chiều (`fv-1`).

## Giới hạn & Cảnh báo an toàn
- **KHÔNG PHẢI CHẨN ĐOÁN LÂM SÀNG:** Các chỉ số đo là phép tính pixel trên ảnh, không phản ánh độ nặng/nhẹ bệnh lý.
- Độ tin cậy (`confidence`) là hàm phân tách độ tương phản histogram và chất lượng ảnh, **tuyệt đối không phải xác suất mắc bệnh**.
- Khi ảnh không đạt Quality Gate (RETAKE) hoặc bộ đo bị lỗi, hệ thống trả về **ABSTAIN** hoặc **MODEL_UNAVAILABLE**, không bao giờ tái sử dụng số liệu cũ.

## Hiệu năng (Benchmark)
- Ground-truth clinical metrics: `N/A — chưa có dữ liệu gán nhãn của bác sĩ, không bịa số liệu`.
