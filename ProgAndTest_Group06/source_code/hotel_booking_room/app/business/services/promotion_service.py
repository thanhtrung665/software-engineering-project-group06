"""Mã khuyến mãi: kiểm tra điều kiện (UC Book room A2) và sổ cái sử dụng (RBLQH07)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.business.domain import round_vnd
from app.business.exceptions import PromotionRejected
from app.core.enums import DiscountType, PromotionStatus, RedemptionStatus
from app.data_access.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class PromotionOutcome:
    promotion_id: int
    promo_code: str
    discount_amount: Decimal
    eligible_room_type_ids: frozenset[int] | None   # None = mọi loại phòng


class PromotionService:
    def evaluate(self, uow: UnitOfWork, *, code: str, account_id: int, nights: int,
                 line_subtotals: dict[int, Decimal], now: datetime, lock: bool) -> PromotionOutcome:
        """line_subtotals: room_type_id -> tổng tiền dòng (trước giảm giá).
        lock=True khóa hàng PROMOTION để kiểm tra hạn mức dưới khóa (lúc tạo booking)."""
        promo = uow.promotions.get_by_code(code, lock=lock)
        if promo is None:
            self._reject("The promotion code does not exist.")
        if promo.promotion_status != PromotionStatus.ACTIVE:
            self._reject("The promotion code is not active.")
        if not (promo.valid_from <= now <= promo.valid_to):
            self._reject("The promotion code is outside its validity period.")
        if nights < promo.min_nights:
            self._reject(f"The promotion requires a minimum stay of {promo.min_nights} night(s).")
        subtotal = sum(line_subtotals.values(), Decimal(0))
        if subtotal < promo.min_order_value:
            self._reject("The booking value is below the minimum required by the promotion.")

        eligible = uow.promotions.eligible_room_type_ids(promo.promotion_id)
        eligible_ids: frozenset[int] | None = frozenset(eligible) if eligible else None
        base = subtotal
        if eligible_ids is not None:
            base = sum((v for rid, v in line_subtotals.items() if rid in eligible_ids), Decimal(0))
            if base == 0:
                self._reject("The promotion does not apply to the selected room types.")

        if promo.total_usage_limit is not None and promo.used_count >= promo.total_usage_limit:
            self._reject("The promotion code has no uses remaining.")
        if uow.promotions.count_account_usage(promo.promotion_id, account_id) >= promo.per_account_limit:
            self._reject("You have reached the usage limit of this promotion code.")

        if promo.discount_type == DiscountType.PERCENT:
            discount = round_vnd(base * promo.discount_value / 100)
            if promo.max_discount is not None:
                discount = min(discount, promo.max_discount)
        else:
            discount = promo.discount_value
        discount = min(round_vnd(discount), base)
        return PromotionOutcome(promo.promotion_id, promo.promo_code, discount, eligible_ids)

    @staticmethod
    def _reject(reason: str):
        raise PromotionRejected(reason, {"field": "promo_code"})


class PromotionLedger:
    """Vòng đời lượt dùng mã: RESERVED (giữ) -> CONSUMED (đã trả tiền) | RELEASED (hoàn lại).
    PROMOTION.used_count luôn cập nhật cùng transaction với PROMOTION_REDEMPTION (RBLQH22)."""

    def reserve(self, uow: UnitOfWork, *, promotion_id: int, account_id: int, booking_id: int,
                discount: Decimal, now: datetime) -> None:
        promo = uow.promotions.get(promotion_id)
        uow.promotions.add_redemption(promotion_id=promotion_id, account_id=account_id, booking_id=booking_id,
                                      discount_amount=discount, redeemed_at=now,
                                      redemption_status=RedemptionStatus.RESERVED)
        promo.used_count += 1

    def release(self, uow: UnitOfWork, booking_id: int) -> bool:
        """Hoàn lại khi hold hết hạn / hủy miễn phí. Idempotent."""
        row = uow.promotions.get_redemption_by_booking(booking_id)
        if row is None or row.redemption_status == RedemptionStatus.RELEASED:
            return False
        if row.redemption_status == RedemptionStatus.RESERVED:
            promo = uow.promotions.get(row.promotion_id)
            promo.used_count = max(0, promo.used_count - 1)
            row.redemption_status = RedemptionStatus.RELEASED
            return True
        return False   # CONSUMED: giữ nguyên (đã thanh toán)

    def consume(self, uow: UnitOfWork, booking_id: int) -> None:
        """Thanh toán thành công: RESERVED -> CONSUMED (used_count không đổi)."""
        row = uow.promotions.get_redemption_by_booking(booking_id)
        if row is not None and row.redemption_status == RedemptionStatus.RESERVED:
            row.redemption_status = RedemptionStatus.CONSUMED

    def reinstate(self, uow: UnitOfWork, booking_id: int) -> None:
        """Thanh toán trễ khôi phục booking: ghi nhận lại lượt dùng KỂ CẢ khi đã chạm total_usage_limit."""
        row = uow.promotions.get_redemption_by_booking(booking_id)
        if row is not None and row.redemption_status == RedemptionStatus.RELEASED:
            uow.promotions.get(row.promotion_id).used_count += 1
            row.redemption_status = RedemptionStatus.CONSUMED
