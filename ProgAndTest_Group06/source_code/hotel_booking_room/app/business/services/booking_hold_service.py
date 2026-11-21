"""UC Book room (bước 7–9, A1, A3, A5, A6) và hủy booking đang giữ phòng (UC Cancel booking A2).

Cơ chế chống overselling: toàn bộ "kiểm tra còn phòng -> tạo booking -> đặt hold_expires_at" nằm trong
MỘT transaction, sau khi đã SELECT ... FOR UPDATE các ROOM_TYPE (id tăng dần). Số phòng trống luôn được
TÍNH LẠI dưới khóa, không dùng số liệu hiển thị trước đó (RBLQH18).
"""
import secrets
from datetime import timedelta
from decimal import Decimal
from typing import Callable

from app.business.clock import Clock
from app.business.domain import StayPeriod
from app.business.dto import BookingDTO, CreateBookingCommand, QuoteCommand, QuoteDTO, RoomSelectionDTO
from app.business.exceptions import (ConflictError, InvalidStateTransition, NotFoundError, PermissionDenied,
                                     PriceChangedError, TooManyPendingBookings, ValidationFailed)
from app.business.services.booking_mapper import BookingMapper
from app.business.services.booking_state import BookingLocker, BookingStateMachine
from app.business.services.inventory_service import InventoryService
from app.business.services.pricing_service import PricingService, ResolvedSelection
from app.business.services.promotion_service import PromotionLedger
from app.business.services.settings_provider import BookingSettingsProvider
from app.core.enums import AccountStatus, BookingSource, BookingStatus, ChangedSource, PaymentStatus, RoleCode, SellingStatus
from app.core.timeutil import vn_today
from app.data_access.unit_of_work import UnitOfWork, run_in_transaction

MAX_ROOMS = 5
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # bỏ ký tự dễ nhầm (0/O, 1/I)


class BookingHoldService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], clock: Clock, *,
                 inventory: InventoryService | None = None, pricing: PricingService | None = None,
                 ledger: PromotionLedger | None = None, state: BookingStateMachine | None = None,
                 mapper: BookingMapper | None = None, settings: BookingSettingsProvider | None = None,
                 locker: BookingLocker | None = None) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._inventory = inventory or InventoryService()
        self._pricing = pricing or PricingService()
        self._ledger = ledger or PromotionLedger()
        self._state = state or BookingStateMachine()
        self._mapper = mapper or BookingMapper()
        self._settings = settings or BookingSettingsProvider()
        self._locker = locker or BookingLocker()

    # ------------------------------------------------------------------ review (bước 4–6, A2)
    def quote(self, account_id: int, cmd: QuoteCommand) -> QuoteDTO:
        """Tính giá + kiểm tra mã khuyến mãi để hiển thị bước Review. KHÔNG giữ phòng, không khóa."""
        now = self._clock.now()
        period = StayPeriod.validated(cmd.check_in_date, cmd.check_out_date, vn_today(now))
        self._validate_rooms_static(cmd.rooms)

        def work(uow: UnitOfWork) -> QuoteDTO:
            settings = self._settings.load(uow)
            self._load_customer(uow, account_id, lock=False)
            selections = self._resolve_selections(uow, cmd.rooms)
            # Search/review availability is an informative snapshot. Final booking repeats
            # the check under SELECT ... FOR UPDATE in create_booking to prevent overselling.
            self._inventory.ensure_available(
                uow, {s.room_type_id: s.quantity for s in selections}, period, now)
            return self._pricing.quote(
                uow, period=period, selections=selections, settings=settings, now=now, account_id=account_id,
                promo_code=cmd.promo_code, deposit_percentage=cmd.deposit_percentage, lock_promotion=False).dto

        return run_in_transaction(self._uow_factory, work, readonly=True)

    # ------------------------------------------------------------------ confirm & hold (bước 7–9)
    def create_booking(self, account_id: int, cmd: CreateBookingCommand) -> BookingDTO:
        if not cmd.accept_terms:
            raise ValidationFailed("You must accept the hotel terms and policies.", {"field": "accept_terms"})
        self._validate_rooms_static(cmd.rooms)

        def work(uow: UnitOfWork) -> BookingDTO:
            now = self._clock.now()                      # tính lại mỗi lần (kể cả khi retry)
            period = StayPeriod.validated(cmd.check_in_date, cmd.check_out_date, vn_today(now))
            settings = self._settings.load(uow)

            # (1) Khóa tài khoản: tuần tự hóa các request của CÙNG user -> giới hạn pending không bị vượt (A5)
            account = self._load_customer(uow, account_id, lock=True)
            selections = self._resolve_selections(uow, cmd.rooms)
            if uow.bookings.count_valid_pending(account_id, now) >= settings.max_pending_bookings:
                raise TooManyPendingBookings(
                    "You already have the maximum number of bookings awaiting payment. "
                    "Please pay for or cancel an existing pending booking first.",
                    {"max_pending_bookings": settings.max_pending_bookings})

            # (2) SELECT ... FOR UPDATE các ROOM_TYPE (id tăng dần) rồi TÍNH LẠI phòng trống dưới khóa (A3)
            self._inventory.lock_inventory(uow, [s.room_type_id for s in selections])
            self._inventory.ensure_available(
                uow, {s.room_type_id: s.quantity for s in selections}, period, now)

            # (3) Tính lại giá dưới khóa (khóa cả mã KM). Giá đổi so với bước review -> yêu cầu xác nhận lại (A6)
            priced = self._pricing.quote(
                uow, period=period, selections=selections, settings=settings, now=now, account_id=account_id,
                promo_code=cmd.promo_code, deposit_percentage=cmd.deposit_percentage, lock_promotion=True)
            quote = priced.dto
            if cmd.expected_total_amount is not None and Decimal(cmd.expected_total_amount) != quote.total_amount:
                raise PriceChangedError(
                    "The price has changed since you reviewed your booking. Please review and confirm again.",
                    {"previous_total_amount": int(cmd.expected_total_amount),
                     "new_total_amount": int(quote.total_amount)})

            # (4) Tạo booking + hold 15 phút, cùng transaction
            booking = self._persist(uow, account, cmd, period, selections, priced, settings, now)
            return self._mapper.to_dto(uow, booking, now)

        return run_in_transaction(self._uow_factory, work)

    # ------------------------------------------------------------------ xem booking / đếm ngược
    def get_booking(self, account_id: int, booking_code: str) -> BookingDTO:
        def work(uow: UnitOfWork) -> BookingDTO:
            booking = uow.bookings.get_by_code(booking_code)
            if booking is None or booking.account_id != account_id:   # chỉ xem booking của mình
                raise NotFoundError(f"Booking {booking_code} not found")
            return self._mapper.to_dto(uow, booking, self._clock.now())

        return run_in_transaction(self._uow_factory, work, readonly=True)

    # ------------------------------------------------------------------ hủy khi còn Pending Payment
    def cancel_pending_booking(self, account_id: int, booking_code: str, reason: str | None = None) -> BookingDTO:
        """UC Cancel booking A2: dừng hold ngay, Cancelled, hoàn mã KM, không hoàn tiền.
        Booking đã Confirmed (phí hủy/hoàn tiền) thuộc luồng Cancel booking đầy đủ – không xử lý ở đây."""
        def work(uow: UnitOfWork) -> BookingDTO:
            now = self._clock.now()
            probe = uow.bookings.get_by_code(booking_code)
            if probe is None or probe.account_id != account_id:
                raise NotFoundError(f"Booking {booking_code} not found")
            booking = self._locker.lock(uow, booking_id=probe.booking_id)
            if booking.booking_status != BookingStatus.PENDING_PAYMENT:
                if booking.booking_status == BookingStatus.CONFIRMED:
                    raise InvalidStateTransition(
                        "A confirmed booking is cancelled through the full cancellation flow "
                        "(fee and refund calculation).")
                raise InvalidStateTransition(
                    "This booking cannot be cancelled online. Please contact the hotel hotline for assistance.")
            self._state.transition(uow, booking, BookingStatus.CANCELLED, source=ChangedSource.USER,
                                   by=account_id, reason=reason or "Cancelled by guest while awaiting payment",
                                   now=now)
            self._ledger.release(uow, booking.booking_id)
            return self._mapper.to_dto(uow, booking, now)

        return run_in_transaction(self._uow_factory, work)

    # ------------------------------------------------------------------ nội bộ
    @staticmethod
    def _validate_rooms_static(rooms: tuple[RoomSelectionDTO, ...]) -> None:
        if not rooms:
            raise ValidationFailed("Select at least one room.", {"field": "rooms"})
        ids = [r.room_type_id for r in rooms]
        if len(ids) != len(set(ids)):
            raise ValidationFailed("Each room type can appear only once; increase its quantity instead.",
                                   {"field": "rooms"})
        if any(r.quantity < 1 or r.adults < 1 or r.children < 0 for r in rooms):
            raise ValidationFailed("Quantity and adults must be at least 1.", {"field": "rooms"})
        total_rooms = sum(r.quantity for r in rooms)
        if total_rooms > MAX_ROOMS:
            raise ValidationFailed(f"A booking is limited to {MAX_ROOMS} rooms.", {"field": "rooms"})
        if sum(r.adults for r in rooms) < total_rooms:
            raise ValidationFailed("Each room needs at least one adult.", {"field": "adults"})

    @staticmethod
    def _load_customer(uow: UnitOfWork, account_id: int, *, lock: bool):
        account = uow.accounts.get_for_update(account_id) if lock else uow.accounts.get(account_id)
        if account is None:
            raise NotFoundError("Account not found")
        if account.role.role_code != RoleCode.CUSTOMER:
            raise PermissionDenied("Only customer accounts can book rooms.")
        if account.account_status != AccountStatus.ACTIVE:
            raise PermissionDenied("Your account is not active.")
        return account

    @staticmethod
    def _resolve_selections(uow: UnitOfWork, rooms: tuple[RoomSelectionDTO, ...]) -> list[ResolvedSelection]:
        types = uow.room_types.get_many([r.room_type_id for r in rooms])
        result = []
        for r in sorted(rooms, key=lambda x: x.room_type_id):          # thứ tự cố định: id tăng dần
            rt = types.get(r.room_type_id)
            if rt is None or rt.selling_status != SellingStatus.ON_SALE:
                raise NotFoundError(f"Room type {r.room_type_id} is not available for sale.")
            if r.adults > r.quantity * rt.max_adults or r.children > r.quantity * rt.max_children:
                raise ValidationFailed(
                    f"Guests exceed the capacity of {r.quantity} x {rt.room_type_code} "
                    f"(max {rt.max_adults} adults and {rt.max_children} children per room).",
                    {"field": "rooms", "room_type_id": r.room_type_id})
            result.append(ResolvedSelection(rt.room_type_id, rt.room_type_code, r.quantity, r.adults, r.children))
        return result

    def _persist(self, uow, account, cmd, period, selections, priced, settings, now):
        quote = priced.dto
        occupant = cmd.occupant
        booking = uow.bookings.create(
            booking_code=self._new_code(uow, now), account_id=account.account_id, created_by=None,
            booking_source=BookingSource.ONLINE, check_in_date=period.check_in, check_out_date=period.check_out,
            adults=sum(s.adults for s in selections), children=sum(s.children for s in selections),
            room_count=sum(s.quantity for s in selections),
            # Người đặt lấy từ tài khoản; người ở (có thể là người khác) lưu ở BOOKING_GUEST
            guest_contact_name=account.full_name, guest_contact_phone=account.phone,
            guest_contact_email=account.email,
            special_requests=(cmd.special_requests or None), estimated_arrival_time=cmd.estimated_arrival_time,
            booking_status=BookingStatus.PENDING_PAYMENT, payment_status=PaymentStatus.UNPAID, currency="VND",
            subtotal_amount=quote.subtotal_amount, discount_amount=quote.discount_amount,
            total_amount=quote.total_amount, deposit_percentage=quote.deposit_percentage,
            deposit_amount=quote.deposit_amount, paid_amount=Decimal(0), remaining_amount=quote.total_amount,
            hold_expires_at=now + timedelta(minutes=settings.hold_minutes),      # GIỮ PHÒNG 15 PHÚT
            policy_snapshot=quote.policy, terms_accepted_at=now)
        for line, sel in zip(quote.lines, selections):
            item = uow.bookings.add_item(
                booking, room_type_id=line.room_type_id, quantity=sel.quantity, adults=sel.adults,
                children=sel.children, line_subtotal=line.line_subtotal, line_discount=line.line_discount,
                line_total=line.line_total)
            for n in line.nights:
                uow.bookings.add_night_rate(
                    item, stay_date=n.stay_date, rate_type_applied=n.rate_type, source_room_rate_id=n.source_room_rate_id,
                    unit_price=n.unit_price, quantity=n.quantity, night_total=n.night_total,
                    night_discount=n.night_discount)
        uow.bookings.add_guest(
            booking, is_primary_guest=True,
            full_name=occupant.full_name if occupant else account.full_name,
            phone=occupant.phone if occupant else account.phone,
            nationality=(occupant.nationality if occupant else None) or account.nationality)
        uow.bookings.flush()                                          # có booking_id
        uow.bookings.add_status_history(
            booking, old_status=None, new_status=BookingStatus.PENDING_PAYMENT, changed_by=account.account_id,
            changed_source=ChangedSource.USER, change_reason="Booking created, rooms held", changed_at=now)
        if priced.promotion is not None:
            self._ledger.reserve(uow, promotion_id=priced.promotion.promotion_id, account_id=account.account_id,
                                 booking_id=booking.booking_id, discount=priced.promotion.discount_amount, now=now)
        uow.bookings.flush()
        return booking

    @staticmethod
    def _new_code(uow: UnitOfWork, now) -> str:
        for _ in range(10):
            suffix = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
            code = f"HB{now:%y%m%d}-{suffix}"
            if not uow.bookings.code_exists(code):
                return code
        raise ConflictError("Could not generate a unique booking code, please retry.")
