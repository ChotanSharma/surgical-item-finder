from abc import ABC, abstractmethod

from app.models import Item, Location


class InventoryAdapter(ABC):
    """What every inventory data source must provide."""

    @abstractmethod
    def list_items(self) -> list[Item]:
        """Return every item in the catalog."""

    @abstractmethod
    def get_item(self, item_number: str) -> Item | None:
        """Return one item, or None if it doesn't exist."""

    @abstractmethod
    def list_locations(self) -> list[Location]:
        """Return every storage location (ORs, cores, ORMC)."""

    def get_location(self, location_id: str) -> Location | None:
        """Shared helper: works for every adapter, built on list_locations()."""
        for location in self.list_locations():
            if location.id == location_id:
                return location
        return None
