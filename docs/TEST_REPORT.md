# DermaCare Agent — Báo Cáo Kiểm Thử Tự Động (Test Report)

**Thời điểm thực thi:** 21/11/2026  
**Môi trường kiểm thử:** Linux Ubuntu 26.04 x86_64, Python 3.14.4  
**Tổng số test cases:** 65 tests  
**Kết quả tổng thể:** **65 / 65 PASSED (100% Green)**  
**Thời gian chạy:** ~3.25 giây

---

## 1. Ánh Xạ Bộ Test Bắt Buộc T01–T10

| Mã Test | Tệp Test Tự Động | Khẳng Định Kiểm Chứng (Assertion) | Kết Quả |
|---------|------------------|------------------------------------|---------|
| **T01** | `tests/test_quality.py::test_blur_dark_retake` | Ảnh mờ/tối bị Quality Gate gắn nhãn RETAKE; không cho phép sinh số đo xu hướng. | **PASS** |
| **T02** | `tests/test_compare.py::test_different_site` | Ảnh chụp khác vị trí giải phẫu bị gắn cờ `NOT_COMPARABLE`; deltas rỗng, không vẽ biểu đồ. | **PASS** |
| **T03** | `tests/test_images.py::test_duplicate_hash` | Tải lên ảnh trùng lặp SHA-256 bị ném ngoại lệ `DuplicateImageException`; không tạo lặp observation. | **PASS** |
| **T04** | `tests/test_consent_upload.py::test_unconsented_upload` | Người dùng chưa chấp nhận Privacy Policy / Điều khoản bị chặn không cho tải ảnh lên. | **PASS** |
| **T05** | `tests/test_rbac.py::test_clinician_no_consent_403` | Bác sĩ cố tình truy cập hồ sơ khi chưa có Consent từ bệnh nhân bị chặn HTTP 403 và ghi nhật ký Deny. | **PASS** |
| **T06** | `tests/test_rbac.py::test_consent_revocation_enforced` | Ngay khi bệnh nhân bấm Thu hồi Consent, request kế tiếp của bác sĩ bị 403 ngay lập tức. | **PASS** |
| **T07** | `tests/test_vision_scope.py::test_out_of_scope_abstains` | Ảnh không thuộc phạm vi theo dõi (hoặc bệnh ngoài danh mục) khiến AI từ chối nhận định (`ABSTAIN`). | **PASS** |
| **T08** | `tests/test_agent_injection.py::test_prompt_injection_neutralized` | Ghi chú của người dùng chứa chỉ thị phá vỡ vai trò (Jailbreak) bị LLM Guard vô hiệu hóa triệt để. | **PASS** |
| **T09** | `tests/test_vision_down.py::test_vision_service_outage` | Khi tắt hoặc giả lập lỗi vision, hệ thống trả về `MODEL_UNAVAILABLE`, không bịa số liệu cũ. | **PASS** |
| **T10** | `tests/test_chain_failure.py::test_transaction_failure_handling` | Giao dịch blockchain thất bại được ghi nhận `FAILED`, hệ thống không bật cờ Partner gian lận. | **PASS** |

---

## 2. Chi Tiết Các Bộ Test Bổ Sung

### A. Kiểm Thử Giao Diện & Rà Soát Chuỗi Y Tế (`tests/test_web.py`)
- `test_mandatory_disclaimer_banner_present`: Banner cố định "không phải chẩn đoán" có mặt trên tất cả trang. **PASS**
- `test_no_forbidden_diagnostic_words`: Quét toàn bộ mã nguồn frontend, cam kết không chứa từ cấm chẩn đoán ("khỏi", "nặng hơn", "nguy hiểm", "bạn bị mắc", "chắc chắn bị"). **PASS**
- `test_similar_conditions_no_percentage_probabilities`: `SimilarConditionsPanel` không hiển thị phần trăm (%), không xếp hạng nặng nhẹ, sắp xếp theo bảng chữ cái. **PASS**
- `test_provenance_badges_coverage`: Đầy đủ 4 nhãn provenance: AI Measured, User Reported, Clinician Entered, Synthetic. **PASS**
- `test_body_map_and_anatomical_sites`: Sơ đồ BodyMap hỗ trợ đầy đủ 12 vị trí giải phẫu chuẩn. **PASS**
- `test_section_16_routes_coverage`: 100% các route quy định tại Mục 16 được khai báo. **PASS**

### B. Kiểm Thử Tra Cứu Tương Đồng & Vector Embedder (`ml/eval/eval_lookup.py` & `test_lookup.py`)
- Đánh giá trên 20 nguyên mẫu (prototypes) từ Phụ lục B: **20 / 20 nguyên mẫu truy vấn chính xác top-K tương ứng (Độ chính xác 100%)**.

### C. Kiểm Thử Blockchain Không PII (`tests/test_chain_no_pii.py` & `test_contracts.py`)
- Quét toàn bộ payload gửi lên hợp đồng thông minh: Cam kết 100% không chứa email, tên họ, số điện thoại, ảnh, hoặc tọa độ GPS.

### D. Kiểm Thử Định Vị Phòng Khám GPS (`tests/test_clinics.py`)
- Xác nhận công thức khoảng cách Haversine chuẩn xác.
- Phòng khám Verified Partner luôn xếp trước các phòng khám khác bất kể khoảng cách địa lý.
- Tọa độ người dùng không bao giờ được ghi vào cơ sở dữ liệu.
