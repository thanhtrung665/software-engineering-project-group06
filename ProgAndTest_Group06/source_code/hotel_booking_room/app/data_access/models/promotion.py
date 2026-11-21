from datetime import datetime
from decimal import Decimal

from sqlalchemy import (Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric,
                        SmallInteger, Unicode, false)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, PkType, utcnow


class Promotion(Base):
    """1.22 PROMOTION"""
    __tablename__ = "promotion"
    __table_args__ = (
        CheckConstraint("discount_type IN ('PERCENT','FIXED')", name="ck_promo_type"),
        CheckConstraint("promotion_status IN ('ACTIVE','PAUSED','EXPIRED')", name="ck_promo_status"),
        CheckConstraint("valid_to > valid_from", name="ck_promo_validity"),
        CheckConstraint("min_nights >= 1 AND per_account_limit >= 1", name="ck_promo_limits"),
    )

    promotion_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    promo_code: Mapped[str] = mapped_column(Unicode(40), unique=True, nullable=False)
    discount_type: Mapped[str] = mapped_column(Unicode(10), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    max_discount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    min_nights: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    min_order_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    valid_to: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_usage_limit: Mapped[int | None] = mapped_column(Integer)
    per_account_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    # Dẫn xuất: số redemption RESERVED/CONSUMED, cập nhật cùng transaction (RBLQH22)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    promotion_status: Mapped[str] = mapped_column(Unicode(15), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    created_by: Mapped[int] = mapped_column(PkType, ForeignKey("account.account_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class PromotionRoomType(Base):
    """1.23 PROMOTION_ROOM_TYPE – không có dòng nào = áp dụng mọi loại phòng."""
    __tablename__ = "promotion_room_type"

    promotion_id: Mapped[int] = mapped_column(PkType, ForeignKey("promotion.promotion_id"),
                                              primary_key=True, autoincrement=False)
    room_type_id: Mapped[int] = mapped_column(PkType, ForeignKey("room_type.room_type_id"),
                                              primary_key=True, autoincrement=False)


class PromotionRedemption(Base):
    """1.24 PROMOTION_REDEMPTION – RESERVED (đang hold) / CONSUMED / RELEASED."""
    __tablename__ = "promotion_redemption"
    __table_args__ = (
        CheckConstraint("redemption_status IN ('RESERVED','CONSUMED','RELEASED')", name="ck_redeem_status"),
    )

    redemption_id: Mapped[int] = mapped_column(PkType, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(PkType, ForeignKey("promotion.promotion_id"),
                                              nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(PkType, ForeignKey("account.account_id"), nullable=False)
    booking_id: Mapped[int] = mapped_column(PkType, ForeignKey("booking.booking_id"),
                                            unique=True, nullable=False)   # RBLB06
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    redemption_status: Mapped[str] = mapped_column(Unicode(15), nullable=False)
