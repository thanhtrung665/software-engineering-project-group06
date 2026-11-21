from decimal import Decimal

from sqlalchemy import Numeric, SmallInteger, Unicode
from sqlalchemy.dialects import mssql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PkType, TimestampMixin


class Hotel(Base, TimestampMixin):
    __tablename__ = "hotel"

    hotel_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    star_rating: Mapped[int] = mapped_column(SmallInteger().with_variant(mssql.TINYINT(), "mssql"),
                                             nullable=False)
    address: Mapped[str] = mapped_column(Unicode(500), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    hotline: Mapped[str] = mapped_column(Unicode(30), nullable=False)
    contact_email: Mapped[str] = mapped_column(Unicode(254), nullable=False)

    room_types: Mapped[list["RoomType"]] = relationship(back_populates="hotel")  # noqa: F821
