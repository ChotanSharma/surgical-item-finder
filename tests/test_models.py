import pytest
from pydantic import ValidationError

from app.models import Item, Location, StockLevel


def test_item_total_stock():
    item = Item(
        item_number="SIF-10001",
        name="Electrosurgical Pencil",
        nicknames=["bovie"],
        category="Electrosurgery",
        stock=[
            StockLevel(location_id="OR-01", quantity=2),
            StockLevel(location_id="ORMC", quantity=40),
        ],
    )
    assert item.total_stock() == 42


def test_negative_stock_is_rejected():
    with pytest.raises(ValidationError):
        StockLevel(location_id="OR-01", quantity=-1)


def test_unknown_location_kind_is_rejected():
    with pytest.raises(ValidationError):
        Location(id="X", name="Parking lot", kind="garage")

