"""Composition root: nơi DUY NHẤT nối các tầng lại với nhau (dependency injection)."""
from typing import Callable

from fastapi import Depends

from app.business.services import RoomTypeService
from app.data_access.database import get_session_factory
from app.data_access.unit_of_work import UnitOfWork


def get_uow_factory() -> Callable[[], UnitOfWork]:
    factory = get_session_factory()
    return lambda: UnitOfWork(factory)


def get_room_type_service(
    uow_factory: Callable[[], UnitOfWork] = Depends(get_uow_factory),
) -> RoomTypeService:
    return RoomTypeService(uow_factory)
