import pytest
from fastapi.testclient import TestClient

from app.composition import get_clock, get_uow_factory
from app.main import app
from tests.support import make_world

BODY = {"check_in_date": "2026-12-01", "check_out_date": "2026-12-03",
        "rooms": [{"room_type_id": 1, "quantity": 1, "adults": 2, "children": 0}],
        "deposit_percentage": "20", "accept_terms": True}


@pytest.fixture()
def api():
    world = make_world()
    app.dependency_overrides[get_uow_factory] = lambda: world.uow_factory
    app.dependency_overrides[get_clock] = lambda: world.clock
    yield TestClient(app), world
    app.dependency_overrides.clear()


def H(account_id): return {"X-Account-Id": str(account_id)}


def test_requires_authentication(api):
    client, _ = api
    assert client.post("/api/v1/bookings", json=BODY).status_code == 401


def test_create_get_and_countdown(api):
    client, world = api
    r = client.post("/api/v1/bookings", json=BODY, headers=H(2))
    assert r.status_code == 201
    b = r.json()
    assert b["booking_status"] == "PENDING_PAYMENT" and b["total_amount"] == 3_600_000
    assert b["deposit_amount"] == 720_000 and b["hold_remaining_seconds"] == 900
    assert b["hold_expires_at"].endswith("+07:00")
    world.clock.advance(minutes=5)
    got = client.get(f"/api/v1/bookings/{b['booking_code']}", headers=H(2)).json()
    assert got["hold_remaining_seconds"] == 600
    assert client.get(f"/api/v1/bookings/{b['booking_code']}", headers=H(3)).status_code == 404


def test_sold_out_returns_409_with_message(api):
    client, _ = api
    body = {**BODY, "rooms": [{"room_type_id": 1, "quantity": 2, "adults": 2}]}
    assert client.post("/api/v1/bookings", json=body, headers=H(2)).status_code == 201
    r = client.post("/api/v1/bookings", json=BODY, headers=H(3))
    assert r.status_code == 409 and r.json()["code"] == "ROOM_SOLD_OUT"
    assert "just sold out" in r.json()["message"]


def test_price_changed_and_validation_codes(api):
    client, _ = api
    r = client.post("/api/v1/bookings", json={**BODY, "expected_total_amount": "1"}, headers=H(2))
    assert r.status_code == 409 and r.json()["code"] == "PRICE_CHANGED"
    assert r.json()["details"]["new_total_amount"] == 3_600_000
    r = client.post("/api/v1/bookings", json={**BODY, "check_in_date": "2026-11-01"}, headers=H(2))
    assert r.status_code == 422 and r.json()["details"]["field"] == "check_in_date"


def test_quote_then_cancel_pending(api):
    client, _ = api
    q = client.post("/api/v1/bookings/quote", json={k: v for k, v in BODY.items() if k != "accept_terms"},
                    headers=H(2)).json()
    assert q["total_amount"] == 3_600_000 and q["vat_included"] and len(q["deposit_options"]) == 3
    code = client.post("/api/v1/bookings", json=BODY, headers=H(2)).json()["booking_code"]
    c = client.post(f"/api/v1/bookings/{code}/cancel-pending", json={"reason": "x"}, headers=H(2))
    assert c.status_code == 200 and c.json()["booking_status"] == "CANCELLED"
    assert client.post(f"/api/v1/bookings/{code}/cancel-pending", headers=H(2)).status_code == 409
