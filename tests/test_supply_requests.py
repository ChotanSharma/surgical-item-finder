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



def test_requests_survive_a_restart(tmp_path):
    db = str(tmp_path / "requests.db")
    inventory = InMemoryAdapter(ITEMS, LOCATIONS)
    saved = RequestStore(inventory, db).create(new_request(SIF_1=2))

    after_restart = RequestStore(inventory, db)  # a brand new store, same file
    assert after_restart.get(saved.id) == saved


def test_first_to_accept_wins(store):
    request = store.create(new_request(SIF_1=1))
    accepted = store.accept(request.id, "Maria")
    assert (accepted.status, accepted.handled_by) == ("accepted", "Maria")
    assert store.accept(request.id, "Sam") is None  # too late
    assert store.get(request.id).handled_by == "Maria"


def test_only_the_accepter_can_deliver(store):
    request = store.create(new_request(SIF_1=1))
    assert store.deliver(request.id, "Maria") is None  # not accepted yet
    store.accept(request.id, "Maria")
    assert store.deliver(request.id, "Sam") is None
    assert store.deliver(request.id, "Maria").status == "delivered"


def test_self_pick_cannot_be_accepted(store):
    request = store.create(new_request("self_pick", SIF_1=1))
    assert store.accept(request.id, "Maria") is None


def test_list_by_status(store):
    waiting = store.create(new_request(SIF_1=1))
    store.create(new_request("self_pick", SIF_1=1))
    assert [r.id for r in store.list(["sent"])] == [waiting.id]


def test_old_database_is_upgraded(tmp_path):
    import sqlite3

    db = str(tmp_path / "old.db")
    old = sqlite3.connect(db)
    old.execute(
        "CREATE TABLE requests (id INTEGER PRIMARY KEY AUTOINCREMENT, or_id TEXT, "
        "fulfillment TEXT, status TEXT, created_at TEXT, lines TEXT)"
    )
    old.commit()
    old.close()
    store = RequestStore(InMemoryAdapter(ITEMS, LOCATIONS), db)
    request = store.create(new_request(SIF_1=1))
    assert store.accept(request.id, "Maria").handled_by == "Maria"



# ---- items we don't stock, sourced by ORMC ----

CUFF = {"company": "Stryker", "model_number": "5921-218-135", "description": "Disposable tourniquet cuff"}


def test_sourcing_line_goes_to_ormc(store):
    request = store.create(NewRequest(
        or_id="OR-01", fulfillment="ormc_delivery", lines=[{"source": CUFF, "quantity": 1}],
    ))
    line = request.lines[0]
    assert request.status == "sent"
    assert line.sourcing is True
    assert line.name == "Disposable tourniquet cuff"
    assert line.pick_from is None
    assert line.pick_from_name == "Not stocked: source from Stryker, model 5921-218-135"
    assert store.get(request.id).lines[0].sourcing is True  # saved and read back


def test_catalog_and_sourcing_lines_mix(store):
    request = store.create(NewRequest(
        or_id="OR-01", fulfillment="ormc_delivery",
        lines=[{"item_number": "SIF-1", "quantity": 1}, {"source": CUFF, "quantity": 2}],
    ))
    assert [line.sourcing for line in request.lines] == [False, True]


def test_sourcing_cannot_be_self_picked():
    with pytest.raises(ValidationError):
        NewRequest(or_id="OR-01", fulfillment="self_pick", lines=[{"source": CUFF, "quantity": 1}])


@pytest.mark.parametrize("line", [
    {"quantity": 1},                                         # neither
    {"item_number": "SIF-1", "source": CUFF, "quantity": 1},  # both
])
def test_line_needs_exactly_one_kind(line):
    with pytest.raises(ValidationError):
        NewRequest(or_id="OR-01", fulfillment="ormc_delivery", lines=[line])
