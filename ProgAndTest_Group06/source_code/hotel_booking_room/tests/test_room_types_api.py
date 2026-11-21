def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_list_only_on_sale_sorted_by_price(client):
    data = client.get("/api/v1/room-types").json()
    assert [r["room_type_code"] for r in data] == ["STANDARD", "DELUXE"]


def test_get_room_type(client):
    assert client.get("/api/v1/room-types/1").status_code == 200


def test_discontinued_and_missing_return_404(client):
    assert client.get("/api/v1/room-types/3").status_code == 404
    r = client.get("/api/v1/room-types/999")
    assert r.status_code == 404 and r.json()["code"] == "NOT_FOUND"
