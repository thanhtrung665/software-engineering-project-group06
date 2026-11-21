"""Dịch lỗi nghiệp vụ -> HTTP response (việc của tầng Presentation)."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.business.exceptions import (BusinessError, ConflictError, NotFoundError,
                                     PermissionDenied, ValidationFailed)

_STATUS = {NotFoundError: 404, ConflictError: 409, ValidationFailed: 422, PermissionDenied: 403}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def business_error_handler(_: Request, exc: BusinessError) -> JSONResponse:
        status = next((s for t, s in _STATUS.items() if isinstance(exc, t)), 400)
        return JSONResponse(status_code=status, content={"code": exc.code, "message": exc.message})
