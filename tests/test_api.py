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


def test_agent_endpoint(monkeypatch):
    from app import main
    from app.agent import AgentResult

    fake = AgentResult(status="not_found", message="Nothing found.", items=[], steps=1)
    monkeypatch.setattr(main, "run_agent", lambda query, inventory: fake)
    response = client.post("/agent/find", json={"query": "unicorn"})
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


def test_agent_endpoint_rejects_empty_query():
    assert client.post("/agent/find", json={"query": ""}).status_code == 422

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Surgical Item Finder" in response.text



def test_availability():
    response = client.get("/items/SIF-10107/availability", params={"or_id": "OR-03"})
    assert response.status_code == 200
    results = response.json()
    assert results, "the bovie pencil should be stocked somewhere"
    minutes = [r["walk_minutes"] for r in results if r["location"]["kind"] != "or"]
    assert minutes == sorted(minutes)


def test_availability_unknown_or():
    response = client.get("/items/SIF-10107/availability", params={"or_id": "OR-99"})
    assert response.status_code == 404


def test_availability_bad_or_format():
    response = client.get("/items/SIF-10107/availability", params={"or_id": "kitchen"})
    assert response.status_code == 422


def test_availability_unknown_item():
    response = client.get("/items/NOPE/availability", params={"or_id": "OR-03"})
    assert response.status_code == 404


def cart(fulfillment="ormc_delivery", or_id="OR-03", item_number="SIF-10107"):
    return {
        "or_id": or_id,
        "fulfillment": fulfillment,
        "lines": [{"item_number": item_number, "quantity": 2}],
    }


def test_send_request_to_ormc():
    response = client.post("/requests", json=cart("ormc_delivery"))
    assert response.status_code == 201
    request = response.json()
    assert request["status"] == "sent"
    assert request["lines"][0]["name"] == "Electrosurgical Pencil, Rocker Switch"
    assert request["id"] in [r["id"] for r in client.get("/requests").json()]


def test_self_pick_request():
    response = client.post("/requests", json=cart("self_pick"))
    assert response.status_code == 201
    assert response.json()["status"] == "self_picked"

def test_request_unknown_item():
    assert client.post("/requests", json=cart(item_number="NOPE")).status_code == 404

def test_request_unknown_or():
    assert client.post("/requests", json=cart(or_id="OR-99")).status_code == 404

def test_request_bad_fulfillment():
    assert client.post("/requests", json=cart(fulfillment="drone")).status_code == 422

def test_missing_item_image_is_404():
    assert client.get("/images/NOPE.webp").status_code == 404
