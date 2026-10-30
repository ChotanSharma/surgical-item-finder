"""Reads inventory from a single JSON file. Used for the demo."""
from __future__ import annotations

import json
from pathlib import Path

from .base import InventoryAdapter
from .models import Item, Location, StockLevel


class JsonInventoryAdapter(InventoryAdapter):
    name = "json"

    def __init__(self, path: str | Path):
        raw = json.loads(Path(path).read_text())
        self._items = [Item(**i) for i in raw["items"]]
        self._locations = [Location(**loc) for loc in raw["locations"]]
        self._stock: dict[str, list[StockLevel]] = {}
        for s in raw["stock"]:
            level = StockLevel(**s)
            self._stock.setdefault(level.item_id, []).append(level)
        self._by_id = {i.id: i for i in self._items}

    def list_items(self) -> list[Item]:
        return list(self._items)

    def list_locations(self) -> list[Location]:
        return list(self._locations)

    def get_stock(self, item_id: str) -> list[StockLevel]:
        return list(self._stock.get(item_id, []))

    def get_item(self, item_id: str) -> Item | None:
        return self._by_id.get(item_id)
