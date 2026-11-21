import unittest
from datetime import date, datetime, time

from app.business.frontdesk import frontdesk_rules as r
from app.business.frontdesk.errors import FrontDeskError

CHECKIN = date(2026, 11, 20)
CUTOFF = time(6, 0)


class CheckInWindow(unittest.TestCase):
    def test_before_00h_of_checkin_date(self):
        with self.assertRaises(FrontDeskError):
            r.check_in_allowed(CHECKIN, datetime(2026, 11, 19, 23, 59), CUTOFF)

    def test_allowed_from_midnight(self):
        r.check_in_allowed(CHECKIN, datetime(2026, 11, 20, 0, 0), CUTOFF)

    def test_allowed_before_cutoff_next_day(self):
        r.check_in_allowed(CHECKIN, datetime(2026, 11, 21, 5, 59), CUTOFF)

    def test_rejected_at_cutoff(self):
        with self.assertRaises(FrontDeskError):
            r.check_in_allowed(CHECKIN, datetime(2026, 11, 21, 6, 0), CUTOFF)


class NoShow(unittest.TestCase):
    def test_not_yet_cutoff(self):
        with self.assertRaises(FrontDeskError):
            r.no_show_allowed(CHECKIN, datetime(2026, 11, 21, 5, 0), CUTOFF)

    def test_after_cutoff(self):
        r.no_show_allowed(CHECKIN, datetime(2026, 11, 21, 6, 0), CUTOFF)

    def test_fee_capped_by_paid(self):  # cọc nhỏ hơn đêm đầu -> mất hết cọc
        self.assertEqual(r.no_show_fee_and_refund(1_000_000, 400_000), (400_000, 0))

    def test_fee_when_fully_paid(self):  # trả đủ -> chỉ mất đêm đầu
        self.assertEqual(r.no_show_fee_and_refund(1_000_000, 3_000_000), (1_000_000, 2_000_000))

    def test_first_night_net_uses_earliest_date_all_rooms(self):
        nights = [
            {"stay_date": date(2026, 11, 20), "night_total": 2_000_000, "night_discount": 200_000},
            {"stay_date": date(2026, 11, 20), "night_total": 1_000_000, "night_discount": 100_000},
            {"stay_date": date(2026, 11, 21), "night_total": 9_000_000, "night_discount": 0},
        ]
        self.assertEqual(r.first_night_net(nights), 2_700_000)

    def test_allocate_refund_across_payments_newest_first(self):
        pays = [{"payment_id": 2, "refundable": 300_000}, {"payment_id": 1, "refundable": 700_000}]
        self.assertEqual(r.allocate_refund(500_000, pays), [(2, 300_000), (1, 200_000)])

    def test_allocate_refund_too_much(self):
        with self.assertRaises(FrontDeskError):
            r.allocate_refund(2_000_000, [{"payment_id": 1, "refundable": 500_000}])


class MoneyRules(unittest.TestCase):
    def test_balance_due(self):
        self.assertEqual(r.balance_due(3_000_000, 150_000, 1_500_000), 1_650_000)

    def test_split_inclusive_vat(self):
        self.assertEqual(r.split_inclusive(1_080_000, 8), 80_000)
        self.assertEqual(r.split_inclusive(1_000_000, 0), 0)

    def test_incidentals(self):
        total = r.validate_incidentals([
            {"item_type": "MINIBAR", "description": "Nước", "quantity": 2, "unit_price": 30_000},
            {"item_type": "LATE_CHECKOUT", "description": "Trễ 2h", "quantity": 1, "unit_price": 200_000}])
        self.assertEqual(total, 260_000)

    def test_incidentals_bad_type(self):
        with self.assertRaises(FrontDeskError):
            r.validate_incidentals([{"item_type": "ROOM", "description": "x", "quantity": 1, "unit_price": 1}])


class Guests(unittest.TestCase):
    def guest(self, name, room, primary=False):
        g = {"full_name": name, "room_id": room, "is_primary": primary}
        if primary:
            g.update(document_type="CITIZEN_ID", document_number="079123456789")
        return g

    def test_ok(self):
        r.validate_guests([self.guest("A", 1, True), self.guest("B", 2)], 2, {1, 2})

    def test_wrong_count(self):
        with self.assertRaises(FrontDeskError):
            r.validate_guests([self.guest("A", 1, True)], 2, {1})

    def test_no_primary(self):
        with self.assertRaises(FrontDeskError):
            r.validate_guests([self.guest("A", 1), self.guest("B", 1)], 2, {1})

    def test_guest_in_unassigned_room(self):
        with self.assertRaises(FrontDeskError):
            r.validate_guests([self.guest("A", 1, True), self.guest("B", 9)], 2, {1})

    def test_primary_missing_document(self):
        g = self.guest("A", 1, True)
        g["document_number"] = None
        with self.assertRaises(FrontDeskError):
            r.validate_guests([g], 1, {1})


if __name__ == "__main__":
    unittest.main()
