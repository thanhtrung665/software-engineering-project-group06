"""Lỗi nghiệp vụ. Tầng Business chỉ ném các lỗi này; Presentation quyết định mã HTTP."""


class BusinessError(Exception):
    code = "BUSINESS_ERROR"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(BusinessError):
    code = "NOT_FOUND"


class ConflictError(BusinessError):  # vd: hết phòng, trùng email
    code = "CONFLICT"


class ValidationFailed(BusinessError):
    code = "VALIDATION_FAILED"


class PermissionDenied(BusinessError):
    code = "FORBIDDEN"


class ConfigurationError(BusinessError):
    """Dữ liệu cấu hình thiếu/sai (vd: loại phòng chưa có giá BASE)."""
    code = "CONFIGURATION_ERROR"


# ---- Book room / hold ----
class RoomSoldOutError(ConflictError):
    """UC Book room A3."""
    code = "ROOM_SOLD_OUT"


class TooManyPendingBookings(ConflictError):
    """UC Book room A5."""
    code = "TOO_MANY_PENDING_BOOKINGS"


class PriceChangedError(ConflictError):
    """UC Book room A6: giá đổi giữa bước review và bước xác nhận -> user phải xác nhận lại."""
    code = "PRICE_CHANGED"


class PromotionRejected(ValidationFailed):
    """UC Book room A2: mã khuyến mãi không hợp lệ (kèm lý do cụ thể)."""
    code = "PROMOTION_INVALID"


class InvalidStateTransition(ConflictError):
    code = "INVALID_STATE_TRANSITION"


# ---- Process payment ----
class PaymentRejected(BusinessError):
    """Callback cổng thanh toán không hợp lệ (sai chữ ký, sai merchant, sai số tiền...). HTTP 400."""
    code = "PAYMENT_REJECTED"


class PaymentGatewayUnavailable(ConfigurationError):
    """Chưa cấu hình thông tin merchant của cổng thanh toán. HTTP 503."""
    code = "PAYMENT_GATEWAY_UNAVAILABLE"
