"""Dịch lỗi nghiệp vụ -> HTTP response (việc của tầng Presentation)."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.business.exceptions import (BusinessError, ConfigurationError, ConflictError, NotFoundError,
                                     PaymentGatewayUnavailable, PermissionDenied, ValidationFailed)

# Thứ tự quan trọng: lớp con đứng trước lớp cha.
_STATUS = {PaymentGatewayUnavailable: 503, NotFoundError: 404, ConflictError: 409, ValidationFailed: 422, PermissionDenied: 403,
           ConfigurationError: 500}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def business_error_handler(_: Request, exc: BusinessError) -> JSONResponse:
        status = next((s for t, s in _STATUS.items() if isinstance(exc, t)), 400)
        body = {"code": exc.code, "message": exc.message}
        if exc.details:
            body["details"] = exc.details
        return JSONResponse(status_code=status, content=body)
