"""Composition root: nơi DUY NHẤT nối các tầng lại với nhau (dependency injection)."""
from typing import Callable

from fastapi import Depends

from app.business.clock import Clock, SystemClock
from app.business.frontdesk.frontdesk_service import FrontDeskService
from app.business.scheduling import HoldExpiryScheduler
from app.business.services import (BookingHoldService, HoldConfirmationService, HoldExpiryService, PaymentService,
                                   RefundService, RoomTypeService)
from app.core.config import get_settings
from app.data_access.database import get_session_factory
from app.data_access.frontdesk.connection import get_connection
from app.data_access.gateways.vnpay_gateway import VnpayGateway
from app.data_access.unit_of_work import UnitOfWork


def get_uow_factory() -> Callable[[], UnitOfWork]:
    factory = get_session_factory()
    return lambda: UnitOfWork(factory)


def get_clock() -> Clock:
    return SystemClock()


def get_room_type_service(
    uow_factory: Callable[[], UnitOfWork] = Depends(get_uow_factory),
) -> RoomTypeService:
    return RoomTypeService(uow_factory)


def get_booking_hold_service(
    uow_factory: Callable[[], UnitOfWork] = Depends(get_uow_factory),
    clock: Clock = Depends(get_clock),
) -> BookingHoldService:
    return BookingHoldService(uow_factory, clock)


def get_hold_expiry_service(
    uow_factory: Callable[[], UnitOfWork] = Depends(get_uow_factory),
    clock: Clock = Depends(get_clock),
) -> HoldExpiryService:
    return HoldExpiryService(uow_factory, clock)


def get_hold_confirmation_service(clock: Clock = Depends(get_clock)) -> HoldConfirmationService:
    """Dành cho service Process payment (cùng transaction với ghi PAYMENT)."""
    return HoldConfirmationService(clock)


def get_payment_gateway() -> VnpayGateway:
    return VnpayGateway()


def get_refund_service(
    uow_factory: Callable[[], UnitOfWork] = Depends(get_uow_factory),
    clock: Clock = Depends(get_clock),
    gateway: VnpayGateway = Depends(get_payment_gateway),
) -> RefundService:
    return RefundService(uow_factory, clock, gateway)


def get_payment_service(
    uow_factory: Callable[[], UnitOfWork] = Depends(get_uow_factory),
    clock: Clock = Depends(get_clock),
    gateway: VnpayGateway = Depends(get_payment_gateway),
    refunds: RefundService = Depends(get_refund_service),
) -> PaymentService:
    return PaymentService(uow_factory, clock, gateway, HoldConfirmationService(clock), refunds)


def get_front_desk_service() -> FrontDeskService:
    return FrontDeskService(get_connection)


def build_hold_expiry_scheduler() -> HoldExpiryScheduler:
    s = get_settings()
    return HoldExpiryScheduler(HoldExpiryService(get_uow_factory(), SystemClock()),
                               s.hold_expiry_interval_seconds)
