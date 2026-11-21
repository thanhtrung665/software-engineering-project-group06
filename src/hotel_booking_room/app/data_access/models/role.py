from sqlalchemy import Unicode
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, PkType


class Role(Base):
    __tablename__ = "role"

    role_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(Unicode(30), unique=True, nullable=False)
    role_name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Unicode(255))
