from pydantic import BaseModel

from app.inventory.base import InventoryAdapter
from app.models import Item, Location

# Where to look first, from the nurse's point of view. Cores come before other
# ORs because other ORs are usually mid-case.
SAME_OR, CORE, ORMC, OTHER_OR = 0, 1, 2, 3


class Availability(BaseModel):
    location: Location
    quantity: int
    walk_minutes: int
    enough: bool  # has at least the quantity requested


def or_number(or_id: str) -> int:
    return int(or_id.split("-")[1])  # "OR-07" -> 7


def core_for(or_id: str) -> str:
    """Core A serves ORs 1-6, Core B serves ORs 7-12."""
    return "CORE-A" if or_number(or_id) <= 6 else "CORE-B"


def priority(from_or: str, location: Location) -> int:
    if location.id == from_or:
        return SAME_OR
    return {"core": CORE, "ormc": ORMC}.get(location.kind, OTHER_OR)


def walk_minutes(from_or: str, location: Location) -> int:
    """Rough walking time in the made-up OR suite."""
    if location.id == from_or:
        return 0
    if location.kind == "core":
        return 1 if location.id == core_for(from_or) else 3
    if location.kind == "ormc":
        return 5
    return 1 + abs(or_number(from_or) - or_number(location.id)) // 2


def check_stock(
    inventory: InventoryAdapter, item: Item, from_or: str, quantity: int = 1
) -> list[Availability]:
    """Every location that has the item, nearest and fullest first."""
    results = []
    for stock in item.stock:
        location = inventory.get_location(stock.location_id)
        if stock.quantity == 0 or location is None:
            continue
        results.append(
            Availability(
                location=location,
                quantity=stock.quantity,
                walk_minutes=walk_minutes(from_or, location),
                enough=stock.quantity >= quantity,
            )
        )
    # Places with enough stock first, then by priority, then by walking time
    results.sort(key=lambda a: (not a.enough, priority(from_or, a.location), a.walk_minutes))
    return results
