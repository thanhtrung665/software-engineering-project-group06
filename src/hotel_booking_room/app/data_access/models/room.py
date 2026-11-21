from sqlalchemy import Boolean, CheckConstraint, ForeignKey, SmallInteger, Unicode, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PkType, TimestampMixin
from .room_type import RoomType


class Room(Base, TimestampMixin):
    __tablename__ = "room"
    __table_args__ = (
        CheckConstraint("room_status IN ('VACANT','OCCUPIED','NEEDS_CLEANING','MAINTENANCE')",
                        name="ck_room_status"),
    )

    room_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    room_type_id: Mapped[int] = mapped_column(PkType,
                                              ForeignKey("room_type.room_type_id"), nullable=False)
    room_number: Mapped[str] = mapped_column(Unicode(20), unique=True, nullable=False)
    floor_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    room_status: Mapped[str] = mapped_column(Unicode(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)

    room_type: Mapped[RoomType] = relationship(back_populates="rooms")
