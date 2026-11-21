from fastapi import FastAPI

from app.core.config import get_settings
from app.presentation.api.v1.router import api_router
from app.presentation.error_handlers import register_error_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    register_error_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
