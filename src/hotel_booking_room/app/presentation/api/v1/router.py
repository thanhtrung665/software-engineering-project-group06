from fastapi import APIRouter

from . import health, room_types

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(room_types.router)
