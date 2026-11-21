from fastapi import APIRouter

from . import bookings, front_desk, health, payments, room_types

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(room_types.router)
api_router.include_router(bookings.router)
api_router.include_router(payments.router)
api_router.include_router(front_desk.router)
