import pytest

from app.inventory.base import InventoryAdapter
from app.inventory.json_adapter import CatalogFile, JsonAdapter
from app.inventory.memory_adapter import InMemoryAdapter
from app.models import Item, Location, StockLevel

LOCATIONS = [
    Location(id="OR-01", name="Operating Room 1", kind="or"),
    Location(id="ORMC", name="OR Materials Core", kind="ormc"),
]

ITEMS = [
    Item(
        item_number="SIF-10001",
        name="Electrosurgical Pencil",
        nicknames=["bovie"],
        category="Electrosurgery",
        stock=[StockLevel(location_id="ORMC", quantity=40)],
    ),
    Item(
        item_number="SIF-10002",
        name="Laparotomy Sponge 18x18",
        nicknames=["laps", "lap pads"],
        category="Sponges",
        unit="pack",
    ),
]


@pytest.fixture(params=["memory", "json"])
def adapter(request, tmp_path):
    if request.param == "memory":
        return InMemoryAdapter(ITEMS, LOCATIONS)
    path = tmp_path / "catalog.json"
    catalog = CatalogFile(items=ITEMS, locations=LOCATIONS)
    path.write_text(catalog.model_dump_json(indent=2), encoding="utf-8")
    return JsonAdapter(path)


def test_list_items(adapter):
    assert len(adapter.list_items()) == 2


def test_get_item_found(adapter):
    assert adapter.get_item("SIF-10001").nicknames == ["bovie"]


def test_get_item_missing_returns_none(adapter):
    assert adapter.get_item("NOPE") is None


def test_get_location(adapter):
    assert adapter.get_location("ORMC").kind == "ormc"
    assert adapter.get_location("OR-99") is None


def test_interface_cannot_be_used_directly():
    with pytest.raises(TypeError):
        InventoryAdapter()
