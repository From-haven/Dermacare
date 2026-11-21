"""
errors.py — Standardized error structures and codes.
Conforms to: {"error": {"code": "...", "message": "...", "details": {}}}
"""
import json

class DermaException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)

DermaCareException = DermaException

class UnauthenticatedException(DermaException):
    def __init__(self, message: str = "Chưa xác thực hoặc token không hợp lệ"):
        super().__init__("UNAUTHENTICATED", message, 401)

class ForbiddenException(DermaException):
    def __init__(self, message: str = "Không có quyền truy cập"):
        super().__init__("FORBIDDEN", message, 403)

class NotFoundException(DermaException):
    def __init__(self, message: str = "Tài nguyên không tìm thấy"):
        super().__init__("NOT_FOUND", message, 404)

class ValidationException(DermaException):
    def __init__(self, message: str = "Dữ liệu không hợp lệ", details: dict = None):
        super().__init__("VALIDATION_ERROR", message, 422, details)

class ConsentRequiredException(DermaException):
    def __init__(self, message: str = "Cần có quyền consent hợp lệ để xem hồ sơ"):
        super().__init__("CONSENT_REQUIRED", message, 403)

class ConsentExpiredException(DermaException):
    def __init__(self, message: str = "Quyền truy cập consent đã hết hạn hoặc bị thu hồi"):
        super().__init__("CONSENT_EXPIRED", message, 403)

class QualityRetakeException(DermaException):
    def __init__(self, message: str = "Ảnh không đạt tiêu chuẩn chất lượng, yêu cầu chụp lại", details: dict = None):
        super().__init__("QUALITY_RETAKE", message, 422, details)

class NotComparableException(DermaException):
    def __init__(self, message: str = "Hai quan sát không thể so sánh được", details: dict = None):
        super().__init__("NOT_COMPARABLE", message, 400, details)

class DuplicateImageException(DermaException):
    def __init__(self, message: str = "Ảnh đã tồn tại trong hệ thống (trùng lặp)"):
        super().__init__("DUPLICATE_IMAGE", message, 409)

class ModelUnavailableException(DermaException):
    def __init__(self, message: str = "Model phân tích hiện không khả dụng"):
        super().__init__("MODEL_UNAVAILABLE", message, 503)

class PartnerRequiredException(DermaException):
    def __init__(self, message: str = "Chỉ phòng khám Verified Partner mới được kích hoạt tính năng này"):
        super().__init__("PARTNER_REQUIRED", message, 403)

class RateLimitedException(DermaException):
    def __init__(self, message: str = "Quá giới hạn tần suất yêu cầu, vui lòng thử lại sau"):
        super().__init__("RATE_LIMITED", message, 429)

class LocationInvalidException(DermaException):
    def __init__(self, message: str = "Toạ độ vị trí không hợp lệ"):
        super().__init__("LOCATION_INVALID", message, 400)
