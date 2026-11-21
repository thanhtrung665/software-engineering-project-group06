from sqlalchemy import func, select

from app.core.enums import RedemptionStatus
from app.data_access.locking import for_update
from app.data_access.models import Promotion, PromotionRedemption, PromotionRoomType
from .base import BaseRepository


class PromotionRepository(BaseRepository[Promotion]):
    model = Promotion

    def get_by_code(self, code: str, *, lock: bool = False) -> Promotion | None:
        stmt = select(Promotion).where(func.lower(Promotion.promo_code) == code.strip().lower())
        promo = self.session.scalar(stmt)
        if promo is None or not lock:
            return promo
        # Khóa theo KHÓA CHÍNH: LOWER() trong câu FOR UPDATE không dùng được index => InnoDB quét và
        # khóa nhiều hàng hơn cần thiết. Tra không khóa trước để lấy id, rồi khóa đúng 1 hàng.
        return self.session.scalar(
            for_update(select(Promotion).where(Promotion.promotion_id == promo.promotion_id), Promotion))

    def eligible_room_type_ids(self, promotion_id: int) -> set[int]:
        return set(self.session.scalars(
            select(PromotionRoomType.room_type_id).where(PromotionRoomType.promotion_id == promotion_id)))

    def count_account_usage(self, promotion_id: int, account_id: int) -> int:
        return self.session.scalar(
            select(func.count()).select_from(PromotionRedemption)
            .where(PromotionRedemption.promotion_id == promotion_id,
                   PromotionRedemption.account_id == account_id,
                   PromotionRedemption.redemption_status.in_(
                       [RedemptionStatus.RESERVED, RedemptionStatus.CONSUMED])))

    def get_redemption_by_booking(self, booking_id: int) -> PromotionRedemption | None:
        return self.session.scalar(
            select(PromotionRedemption).where(PromotionRedemption.booking_id == booking_id))

    def add_redemption(self, **fields) -> PromotionRedemption:
        row = PromotionRedemption(**fields)
        self.session.add(row)
        return row
