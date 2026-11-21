"""Lỗi nghiệp vụ. Tầng Business chỉ ném các lỗi này; Presentation quyết định mã HTTP."""


class BusinessError(Exception):
    code = "BUSINESS_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(BusinessError):
    code = "NOT_FOUND"


class ConflictError(BusinessError):  # vd: hết phòng, trùng email
    code = "CONFLICT"


class ValidationFailed(BusinessError):
    code = "VALIDATION_FAILED"


class PermissionDenied(BusinessError):
    code = "FORBIDDEN"
