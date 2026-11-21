from fastapi import APIRouter, Depends

from app.business.services import RoomTypeService
from app.composition import get_room_type_service
from app.presentation.schemas.room_type import RoomTypeResponse

router = APIRouter(prefix="/room-types", tags=["room-types"])


@router.get("", response_model=list[RoomTypeResponse])
def list_room_types(service: RoomTypeService = Depends(get_room_type_service)):
    return service.list_on_sale()


@router.get("/{room_type_id}", response_model=RoomTypeResponse)
def get_room_type(room_type_id: int, service: RoomTypeService = Depends(get_room_type_service)):
    return service.get(room_type_id)
