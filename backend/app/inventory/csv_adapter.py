"""Reads inventory from three CSV files, the format most inventory systems can export.

items.csv      id,item_number,name,category,nicknames,unit,image_url   (nicknames separated by |)
locations.csv  id,name,type,x,y,serves                                  (serves separated by |)
stock.csv      item_id,location_id,quantity,bin
"""
from __future__ import annotations

import csv
from pathlib import Path

from .base import InventoryAdapter
from .models import Item, Location, StockLevel


def _split(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split("|") if v.strip()]


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class CsvInventoryAdapter(InventoryAdapter):
    name = "csv"

    def __init__(self, folder: str | Path):
        folder = Path(folder)
        self._items = [
            Item(
                id=r["id"], item_number=r["item_number"], name=r["name"],
                category=r["category"], nicknames=_split(r.get("nicknames")),
                unit=r.get("unit") or "each", image_url=r.get("image_url") or None,
            )
            for r in _read(folder / "items.csv")
        ]
        self._locations = [
            Location(
                id=r["id"], name=r["name"], type=r["type"],
                x=float(r["x"]), y=float(r["y"]), serves=_split(r.get("serves")),
            )
            for r in _read(folder / "locations.csv")
        ]
        self._stock: dict[str, list[StockLevel]] = {}
        for r in _read(folder / "stock.csv"):
            level = StockLevel(
                item_id=r["item_id"], location_id=r["location_id"],
                quantity=int(r["quantity"]), bin=r.get("bin") or None,
            )
            self._stock.setdefault(level.item_id, []).append(level)

    def list_items(self) -> list[Item]:
        return list(self._items)

    def list_locations(self) -> list[Location]:
        return list(self._locations)

    def get_stock(self, item_id: str) -> list[StockLevel]:
        return list(self._stock.get(item_id, []))
