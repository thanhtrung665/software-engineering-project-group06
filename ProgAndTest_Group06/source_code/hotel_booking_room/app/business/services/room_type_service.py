from typing import Callable

from app.business.dto import RoomTypeDTO
from app.business.exceptions import NotFoundError
from app.core.enums import SellingStatus
from app.data_access.unit_of_work import UnitOfWork


def _to_dto(e) -> RoomTypeDTO:
    return RoomTypeDTO(
        room_type_id=e.room_type_id, room_type_code=e.room_type_code, area_sqm=e.area_sqm,
        bed_type=e.bed_type, max_adults=e.max_adults, max_children=e.max_children,
        view_direction=e.view_direction, breakfast_included=e.breakfast_included,
        base_price=e.base_price, selling_status=e.selling_status,
    )


class RoomTypeService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def list_on_sale(self) -> list[RoomTypeDTO]:
        with self._uow_factory() as uow:
            return [_to_dto(e) for e in uow.room_types.list_by_status(SellingStatus.ON_SALE)]

    def get(self, room_type_id: int) -> RoomTypeDTO:
        with self._uow_factory() as uow:
            entity = uow.room_types.get(room_type_id)
            if entity is None or entity.selling_status != SellingStatus.ON_SALE:
                raise NotFoundError(f"Room type {room_type_id} not found")
            return _to_dto(entity)
