from sqlalchemy import select

from app.data_access.models import RoomType
from .base import BaseRepository


class RoomTypeRepository(BaseRepository[RoomType]):
    model = RoomType

    def list_by_status(self, selling_status: str) -> list[RoomType]:
        stmt = (select(RoomType)
                .where(RoomType.selling_status == selling_status)
                .order_by(RoomType.base_price))
        return list(self.session.scalars(stmt))

    def get_by_code(self, code: str) -> RoomType | None:
        return self.session.scalar(select(RoomType).where(RoomType.room_type_code == code))
