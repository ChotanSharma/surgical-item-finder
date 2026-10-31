from app.inventory.base import InventoryAdapter
from app.models import Item, Location


class InMemoryAdapter(InventoryAdapter):
    """Holds items and locations in memory."""

    def __init__(self, items: list[Item], locations: list[Location]):
        self._items = {item.item_number: item for item in items}
        self._locations = list(locations)

    def list_items(self) -> list[Item]:
        return list(self._items.values())

    def get_item(self, item_number: str) -> Item | None:
        return self._items.get(item_number)

    def list_locations(self) -> list[Location]:
        return list(self._locations)
