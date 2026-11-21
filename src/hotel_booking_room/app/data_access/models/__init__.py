"""Import tất cả model để Base.metadata biết đủ bảng (create_all / Alembic)."""
from .account import Account
from .base import Base
from .hotel import Hotel
from .role import Role
from .room import Room
from .room_type import RoomType

__all__ = ["Base", "Role", "Account", "Hotel", "RoomType", "Room"]
