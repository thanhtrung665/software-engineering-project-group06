"""DTO của tầng Business: tầng trên không phải biết ORM entity."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RoomTypeDTO:
    room_type_id: int
    room_type_code: str
    area_sqm: Decimal
    bed_type: str
    max_adults: int
    max_children: int
    view_direction: str | None
    breakfast_included: bool
    base_price: Decimal
    selling_status: str
