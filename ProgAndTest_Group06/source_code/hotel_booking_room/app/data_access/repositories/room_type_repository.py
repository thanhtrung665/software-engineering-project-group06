from sqlalchemy import select

from app.data_access.locking import for_update
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

    def get_many(self, room_type_ids) -> dict[int, RoomType]:
        stmt = select(RoomType).where(RoomType.room_type_id.in_(list(room_type_ids)))
        return {rt.room_type_id: rt for rt in self.session.scalars(stmt)}

    def lock_for_update(self, room_type_ids) -> list[RoomType]:
        """Khóa bản ghi điều phối tồn kho (ROOM_TYPE) theo thứ tự room_type_id TĂNG DẦN.

        Mỗi hàng khóa bằng một câu SELECT riêng để thứ tự lấy khóa chắc chắn tăng dần
        (RBLQH18) – mọi transaction cùng thứ tự => không deadlock vòng tròn.
        """
        locked = []
        for rid in sorted(set(room_type_ids)):
            row = self.session.scalar(
                for_update(select(RoomType).where(RoomType.room_type_id == rid), RoomType))
            if row is not None:
                locked.append(row)
        return locked
