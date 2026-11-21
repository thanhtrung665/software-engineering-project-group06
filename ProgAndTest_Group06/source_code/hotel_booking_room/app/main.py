from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.composition import build_hold_expiry_scheduler
from app.core.config import get_settings
from app.presentation.api.v1.router import api_router
from app.presentation.error_handlers import register_error_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Khởi động job nền giải phóng phòng giữ quá 15 phút."""
    scheduler = build_hold_expiry_scheduler() if get_settings().hold_expiry_scheduler_enabled else None
    if scheduler:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler:
            scheduler.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
