"""Tính giá: giá từng đêm (snapshot), khuyến mãi, tiền cọc (UC Book room bước 4–6, A2)."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.business.domain import RateBook, RateRule, StayPeriod, allocate_pro_rata, round_vnd
from app.business.dto import DepositOptionDTO, NightPriceDTO, QuoteDTO, QuoteLineDTO
from app.business.exceptions import ValidationFailed
from app.business.services.promotion_service import PromotionOutcome, PromotionService
from app.business.services.settings_provider import BookingSettings
from app.data_access.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class ResolvedSelection:
    """Một dòng phòng đã kiểm tra: loại phòng + số lượng + khách."""
    room_type_id: int
    room_type_code: str
    quantity: int
    adults: int
    children: int


@dataclass(frozen=True)
class PricedQuote:
    """Kết quả nội bộ: DTO để trả ra + thông tin để lưu booking."""
    dto: QuoteDTO
    promotion: PromotionOutcome | None


class DepositPolicy:
    """Mức cọc do Admin cấu hình (DEPOSIT_LEVEL); tiền cọc làm tròn 1 VND."""

    def options(self, uow: UnitOfWork, now: datetime) -> list[Decimal]:
        return uow.deposit_levels.list_active_percentages(now)

    def validate(self, percentage: Decimal, available: list[Decimal]) -> Decimal:
        if percentage not in available:
            raise ValidationFailed("The selected deposit level is not available.",
                                   {"field": "deposit_percentage",
                                    "allowed": [str(p.normalize()) for p in available]})
        return percentage

    @staticmethod
    def amount(total: Decimal, percentage: Decimal) -> Decimal:
        return round_vnd(total * percentage / 100)


class PricingService:
    def __init__(self, promotions: PromotionService | None = None, deposits: DepositPolicy | None = None) -> None:
        self._promotions = promotions or PromotionService()
        self._deposits = deposits or DepositPolicy()

    def quote(self, uow: UnitOfWork, *, period: StayPeriod, selections: list[ResolvedSelection],
              settings: BookingSettings, now: datetime, account_id: int, promo_code: str | None,
              deposit_percentage: Decimal | None, lock_promotion: bool) -> PricedQuote:
        books = self._load_rate_books(uow, [s.room_type_id for s in selections], period)

        # 1) Giá từng đêm × số phòng (giá đã gồm VAT/phí – không cộng thêm)
        raw: list[tuple[ResolvedSelection, list[tuple]]] = []
        line_subtotals: dict[int, Decimal] = {}
        for sel in selections:
            nights = []
            for night in period.night_dates:
                r = books[sel.room_type_id].resolve(night)
                nights.append((night, r, round_vnd(r.price * sel.quantity)))
            raw.append((sel, nights))
            line_subtotals[sel.room_type_id] = sum((n[2] for n in nights), Decimal(0))
        subtotal = sum(line_subtotals.values(), Decimal(0))

        # 2) Khuyến mãi
        outcome = None
        if promo_code and promo_code.strip():
            outcome = self._promotions.evaluate(
                uow, code=promo_code, account_id=account_id, nights=period.nights,
                line_subtotals=line_subtotals, now=now, lock=lock_promotion)
        discount = outcome.discount_amount if outcome else Decimal(0)

        # 3) Chia giảm giá theo tỉ lệ cho từng (dòng, đêm); dư dồn vào dòng/đêm cuối
        cells = [(i, j) for i, (_, nights) in enumerate(raw) for j in range(len(nights))]
        weights = []
        for i, j in cells:
            sel, nights = raw[i]
            eligible = outcome is None or outcome.eligible_room_type_ids is None \
                or sel.room_type_id in outcome.eligible_room_type_ids
            weights.append(int(nights[j][2]) if eligible else 0)
        shares = dict(zip(cells, allocate_pro_rata(int(discount), weights)))

        lines = []
        for i, (sel, nights) in enumerate(raw):
            night_dtos = tuple(
                NightPriceDTO(stay_date=n[0], rate_type=n[1].rate_type, unit_price=n[1].price,
                              quantity=sel.quantity, night_total=n[2],
                              night_discount=Decimal(shares[(i, j)]), source_room_rate_id=n[1].rate_id)
                for j, n in enumerate(nights))
            line_sub = sum((n.night_total for n in night_dtos), Decimal(0))
            line_disc = sum((n.night_discount for n in night_dtos), Decimal(0))
            lines.append(QuoteLineDTO(
                room_type_id=sel.room_type_id, room_type_code=sel.room_type_code, quantity=sel.quantity,
                adults=sel.adults, children=sel.children, nights=night_dtos,
                line_subtotal=line_sub, line_discount=line_disc, line_total=line_sub - line_disc))
        total = subtotal - discount

        # 4) Tiền cọc
        available = self._deposits.options(uow, now)
        options = tuple(DepositOptionDTO(p, DepositPolicy.amount(total, p),
                                         total - DepositPolicy.amount(total, p)) for p in available)
        dep_pct = dep_amt = balance = None
        if deposit_percentage is not None:
            dep_pct = self._deposits.validate(deposit_percentage, available)
            dep_amt = DepositPolicy.amount(total, dep_pct)
            balance = total - dep_amt

        dto = QuoteDTO(
            check_in_date=period.check_in, check_out_date=period.check_out, nights=period.nights,
            lines=tuple(lines), subtotal_amount=subtotal, discount_amount=discount, total_amount=total,
            promo_code=outcome.promo_code if outcome else None, deposit_options=options,
            deposit_percentage=dep_pct, deposit_amount=dep_amt, balance_at_check_in=balance,
            policy=settings.policy_snapshot())
        return PricedQuote(dto, outcome)

    @staticmethod
    def _load_rate_books(uow: UnitOfWork, room_type_ids, period: StayPeriod) -> dict[int, RateBook]:
        rates = uow.rates.active_rates(room_type_ids)
        holidays = uow.rates.holiday_dates_by_rate([r.room_rate_id for r in rates if r.rate_type == "HOLIDAY"])
        by_type: dict[int, list[RateRule]] = {rid: [] for rid in room_type_ids}
        for r in rates:
            by_type[r.room_type_id].append(RateRule(
                rate_id=r.room_rate_id, rate_type=r.rate_type, price=r.nightly_price, start=r.start_date,
                end=r.end_date, weekday_no=r.weekday_no,
                holiday_dates=frozenset(holidays.get(r.room_rate_id, ()))))
        return {rid: RateBook(rid, rules) for rid, rules in by_type.items()}
