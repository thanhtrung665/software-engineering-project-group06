from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RoomTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
