"""Reads inventory from a SQL database through configurable queries.

Works with any Python DB-API connection (sqlite3, psycopg, pyodbc for SQL Server, ...).
Each hospital's schema is different, so the three queries are settings, not code.
Each query must return columns named like the fields in models.py.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Callable

from .base import InventoryAdapter
from .models import Item, Location, StockLevel

DEFAULT_QUERIES = {
    "items": "SELECT id, item_number, name, category, nicknames, unit, image_url FROM items",
    "locations": "SELECT id, name, type, x, y, serves FROM locations",
    "stock": "SELECT item_id, location_id, quantity, bin FROM stock WHERE item_id = ?",
}


def _split(value: Any) -> list[str]:
    return [v.strip() for v in str(value or "").split("|") if v.strip()]


class SqlInventoryAdapter(InventoryAdapter):
    name = "sql"

    def __init__(self, connect: Callable[[], Any], queries: dict[str, str] | None = None):
        self._connect = connect
        self._q = {**DEFAULT_QUERIES, **(queries or {})}

    @classmethod
    def sqlite(cls, path: str, queries: dict[str, str] | None = None) -> "SqlInventoryAdapter":
        return cls(lambda: sqlite3.connect(path), queries)

    def _rows(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            conn.close()

    def list_items(self) -> list[Item]:
        return [
            Item(**{**r, "nicknames": _split(r.get("nicknames")), "unit": r.get("unit") or "each"})
            for r in self._rows(self._q["items"])
        ]

    def list_locations(self) -> list[Location]:
        return [Location(**{**r, "serves": _split(r.get("serves"))}) for r in self._rows(self._q["locations"])]

    def get_stock(self, item_id: str) -> list[StockLevel]:
        return [StockLevel(**r) for r in self._rows(self._q["stock"], (item_id,))]
