import pytest
from pydantic import ValidationError

from app.inventory.memory_adapter import InMemoryAdapter
from app.models import Item, Location, StockLevel
from app.supply_requests import NewRequest, RequestStore, UnknownItemError

LOCATIONS = [
    Location(id="OR-01", name="Operating Room 1", kind="or"),
    Location(id="CORE-A", name="Core A", kind="core"),
    Location(id="ORMC", name="OR Materials Core", kind="ormc"),
]
ITEMS = [
    Item(
        item_number="SIF-1",
        name="Bovie Pencil",
        category="Electrosurgery",
        stock=[
            StockLevel(location_id="CORE-A", quantity=2),
            StockLevel(location_id="ORMC", quantity=50),
        ],
    ),
    Item(item_number="SIF-2", name="Out Of Stock Thing", category="Test"),
]


@pytest.fixture
def store():
    return RequestStore(InMemoryAdapter(ITEMS, LOCATIONS))


def new_request(fulfillment="ormc_delivery", **lines):
    """new_request(SIF_1=2) -> request for 2 of SIF-1 from OR-01."""
    return NewRequest(
        or_id="OR-01",
        fulfillment=fulfillment,
        lines=[{"item_number": k.replace("_", "-"), "quantity": v} for k, v in lines.items()],
    )


def test_delivery_request_is_sent(store):
    request = store.create(new_request("ormc_delivery", SIF_1=1))
    assert request.id == 1
    assert request.status == "sent"
    assert request.lines[0].pick_from == "CORE-A"


def test_self_pick_is_recorded_but_not_sent(store):
    request = store.create(new_request("self_pick", SIF_1=1))
    assert request.status == "self_picked"
    assert store.list() == [request]


def test_pick_from_has_enough_stock(store):
    request = store.create(new_request(SIF_1=5))  # Core A only has 2
    assert request.lines[0].pick_from == "ORMC"


def test_nowhere_has_enough(store):
    request = store.create(new_request(SIF_2=1))
    assert request.lines[0].pick_from is None


def test_ids_count_up_and_list_is_newest_first(store):
    first = store.create(new_request(SIF_1=1))
    second = store.create(new_request(SIF_1=1))
    assert (first.id, second.id) == (1, 2)
    assert [r.id for r in store.list()] == [2, 1]
    assert store.get(1) == first
    assert store.get(99) is None


def test_unknown_item_is_rejected(store):
    with pytest.raises(UnknownItemError):
        store.create(new_request(NOPE=1))


def test_empty_cart_is_rejected():
    with pytest.raises(ValidationError):
        NewRequest(or_id="OR-01", fulfillment="self_pick", lines=[])
