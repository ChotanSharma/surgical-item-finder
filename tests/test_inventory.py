import csv
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.inventory import build_adapter
from app.inventory.csv_adapter import CsvInventoryAdapter
from app.inventory.sql_adapter import SqlInventoryAdapter
from app.main import app

CATALOG = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


@pytest.fixture(scope="module")
def raw():
    return json.loads(CATALOG.read_text())


def test_catalog_is_large_and_consistent(raw):
    assert len(raw["items"]) >= 250
    item_ids = {i["id"] for i in raw["items"]}
    loc_ids = {loc["id"] for loc in raw["locations"]}
    assert len({i["item_number"] for i in raw["items"]}) == len(raw["items"])
    assert all(s["item_id"] in item_ids and s["location_id"] in loc_ids for s in raw["stock"])
    # every item is stocked in the ORMC
    in_ormc = {s["item_id"] for s in raw["stock"] if s["location_id"] == "ORMC"}
    assert in_ormc == item_ids


def test_json_adapter():
    inv = build_adapter("json", str(CATALOG))
    item = inv.list_items()[0]
    assert inv.get_item(item.id) == item
    assert inv.find_by_item_number(item.item_number) == item
    assert any(s.location_id == "ORMC" for s in inv.get_stock(item.id))


def _export(raw, tmp_path):
    """Write the demo catalog as CSV files and a SQLite db, like a hospital export."""
    with open(tmp_path / "items.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["id", "item_number", "name", "category", "nicknames", "unit", "image_url"])
        w.writeheader()
        for i in raw["items"]:
            w.writerow({**i, "nicknames": "|".join(i["nicknames"]), "image_url": i["image_url"] or ""})
    with open(tmp_path / "locations.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["id", "name", "type", "x", "y", "serves"])
        w.writeheader()
        for loc in raw["locations"]:
            w.writerow({**loc, "serves": "|".join(loc["serves"])})
    with open(tmp_path / "stock.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["item_id", "location_id", "quantity", "bin"])
        w.writeheader()
        w.writerows(raw["stock"])

    db = tmp_path / "inv.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE items (id, item_number, name, category, nicknames, unit, image_url)")
    con.execute("CREATE TABLE locations (id, name, type, x, y, serves)")
    con.execute("CREATE TABLE stock (item_id, location_id, quantity, bin)")
    con.executemany("INSERT INTO items VALUES (?,?,?,?,?,?,?)",
                    [(i["id"], i["item_number"], i["name"], i["category"], "|".join(i["nicknames"]), i["unit"], None)
                     for i in raw["items"]])
    con.executemany("INSERT INTO locations VALUES (?,?,?,?,?,?)",
                    [(l["id"], l["name"], l["type"], l["x"], l["y"], "|".join(l["serves"])) for l in raw["locations"]])
    con.executemany("INSERT INTO stock VALUES (?,?,?,?)",
                    [(s["item_id"], s["location_id"], s["quantity"], s["bin"]) for s in raw["stock"]])
    con.commit()
    con.close()
    return db


def test_all_adapters_return_the_same_data(raw, tmp_path):
    db = _export(raw, tmp_path)
    adapters = [build_adapter("json", str(CATALOG)), CsvInventoryAdapter(tmp_path), SqlInventoryAdapter.sqlite(str(db))]
    first = adapters[0]
    for other in adapters[1:]:
        assert other.list_items() == first.list_items()
        assert other.list_locations() == first.list_locations()
        item_id = first.list_items()[42].id
        key = lambda s: s.location_id
        assert sorted(other.get_stock(item_id), key=key) == sorted(first.get_stock(item_id), key=key)


def test_api():
    client = TestClient(app)
    assert client.get("/api/health").json()["status"] == "ok"
    hits = client.get("/api/items", params={"q": "lap sponge"}).json()
    assert any("Laparotomy Sponge" in h["name"] for h in hits)
    stock = client.get(f"/api/items/{hits[0]['id']}/stock").json()
    assert stock
    assert client.get("/api/items/NOPE").status_code == 404
    assert len(client.get("/api/locations").json()) == 15
    assert "Surgical Item Finder" in client.get("/").text
