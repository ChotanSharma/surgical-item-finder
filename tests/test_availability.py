from app.availability import check_stock, core_for, walk_minutes
from app.inventory.memory_adapter import InMemoryAdapter
from app.models import Item, Location, StockLevel

LOCATIONS = [
    Location(id="OR-01", name="Operating Room 1", kind="or"),
    Location(id="OR-02", name="Operating Room 2", kind="or"),
    Location(id="OR-08", name="Operating Room 8", kind="or"),
    Location(id="CORE-A", name="Core A", kind="core"),
    Location(id="CORE-B", name="Core B", kind="core"),
    Location(id="ORMC", name="OR Materials Core", kind="ormc"),
]
BY_ID = {loc.id: loc for loc in LOCATIONS}


def make_item(**stock):
    """make_item(OR_01=2, ORMC=40) -> item with that stock."""
    return Item(
        item_number="SIF-1",
        name="Test Item",
        category="Test",
        stock=[StockLevel(location_id=k.replace("_", "-"), quantity=v) for k, v in stock.items()],
    )


def order(results):
    return [a.location.id for a in results]


def test_core_for():
    assert core_for("OR-06") == "CORE-A"
    assert core_for("OR-07") == "CORE-B"


def test_walk_minutes():
    assert walk_minutes("OR-01", BY_ID["OR-01"]) == 0
    assert walk_minutes("OR-01", BY_ID["CORE-A"]) == 1
    assert walk_minutes("OR-01", BY_ID["CORE-B"]) == 3
    assert walk_minutes("OR-01", BY_ID["ORMC"]) == 5


def test_nearest_first():
    item = make_item(OR_08=5, ORMC=40, CORE_B=3, OR_02=1, CORE_A=2, OR_01=1)
    inventory = InMemoryAdapter([item], LOCATIONS)
    results = check_stock(inventory, item, "OR-01")
    assert order(results) == ["OR-01", "CORE-A", "CORE-B", "ORMC", "OR-02", "OR-08"]


def test_own_core_depends_on_or():
    item = make_item(CORE_A=5, CORE_B=5)
    inventory = InMemoryAdapter([item], LOCATIONS)
    assert order(check_stock(inventory, item, "OR-08")) == ["CORE-B", "CORE-A"]


def test_places_with_enough_come_first():
    item = make_item(CORE_A=2, ORMC=40)
    inventory = InMemoryAdapter([item], LOCATIONS)
    results = check_stock(inventory, item, "OR-01", quantity=5)
    assert order(results) == ["ORMC", "CORE-A"]
    assert [a.enough for a in results] == [True, False]


def test_empty_locations_are_skipped():
    item = make_item(CORE_A=0, ORMC=10)
    inventory = InMemoryAdapter([item], LOCATIONS)
    assert order(check_stock(inventory, item, "OR-01")) == ["ORMC"]
