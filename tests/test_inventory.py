import pytest

from app.inventory.base import InventoryAdapter
from app.inventory.memory_adapter import InMemoryAdapter
from app.models import Item, Location, StockLevel


@pytest.fixture
def adapter():
    locations = [
        Location(id="OR-01", name="Operating Room 1", kind="or"),
        Location(id="ORMC", name="OR Materials Core", kind="ormc"),
    ]
    items = [
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
    return InMemoryAdapter(items, locations)


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
