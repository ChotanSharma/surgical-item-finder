from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_search_endpoint():
    response = client.get("/items/search", params={"q": "bovie"})
    assert response.status_code == 200
    assert "bovie" in response.json()[0]["item"]["nicknames"]


def test_search_requires_query():
    assert client.get("/items/search").status_code == 422


def test_get_item():
    response = client.get("/items/SIF-10001")
    assert response.status_code == 200
    assert response.json()["item_number"] == "SIF-10001"


def test_get_item_missing():
    assert client.get("/items/NOPE").status_code == 404


def test_locations():
    assert len(client.get("/locations").json()) == 15
