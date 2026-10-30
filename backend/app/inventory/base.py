"""The one interface the app and the agent use to talk to any inventory system.

To connect a new system (Epic, Lawson, PAR Excellence, a SQL database, ...),
write a class that implements InventoryAdapter and register it in factory.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .models import Item, Location, StockLevel


class InventoryAdapter(ABC):
    """Read-only view of a hospital's supply inventory."""

    name: str = "base"

    @abstractmethod
    def list_items(self) -> list[Item]:
        """Every item in the catalog."""

    @abstractmethod
    def list_locations(self) -> list[Location]:
        """Every place items are stored: OR carts, cores and the ORMC."""

    @abstractmethod
    def get_stock(self, item_id: str) -> list[StockLevel]:
        """Stock of one item at every location that holds it."""

    # Helpers built on the methods above. Adapters can override them
    # with faster native queries if their source supports it.

    def get_item(self, item_id: str) -> Item | None:
        return next((i for i in self.list_items() if i.id == item_id), None)

    def get_location(self, location_id: str) -> Location | None:
        return next((loc for loc in self.list_locations() if loc.id == location_id), None)

    def find_by_item_number(self, item_number: str) -> Item | None:
        return next((i for i in self.list_items() if i.item_number == item_number), None)
