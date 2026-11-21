from decimal import Decimal

from sqlalchemy import (Boolean, CheckConstraint, ForeignKey, Numeric,
                        SmallInteger, Unicode, false)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PkType, TimestampMixin
from .hotel import Hotel


class RoomType(Base, TimestampMixin):
    __tablename__ = "room_type"
    __table_args__ = (
        CheckConstraint("selling_status IN ('ON_SALE','DISCONTINUED')", name="ck_room_type_selling_status"),
    )

    room_type_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    hotel_id: Mapped[int] = mapped_column(PkType,
                                          ForeignKey("hotel.hotel_id"), nullable=False)
    room_type_code: Mapped[str] = mapped_column(Unicode(30), unique=True, nullable=False)
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False)
    bed_type: Mapped[str] = mapped_column(Unicode(30), nullable=False)
    max_adults: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    max_children: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    view_direction: Mapped[str | None] = mapped_column(Unicode(50))
    breakfast_included: Mapped[bool] = mapped_column(Boolean, default=False,
                                                     server_default=false(), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    selling_status: Mapped[str] = mapped_column(Unicode(20), nullable=False)

    hotel: Mapped[Hotel] = relationship(back_populates="room_types")
    rooms: Mapped[list["Room"]] = relationship(back_populates="room_type")  # noqa: F821
