"""Surgical Item Finder API.

Day 1: inventory endpoints on top of the adapter layer.
The AI agent search arrives on Day 2.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .inventory import InventoryAdapter, Item, Location, StockLevel, build_adapter

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(title="Surgical Item Finder", version="0.1.0")


@lru_cache
def inventory() -> InventoryAdapter:
    return build_adapter()


@app.get("/api/health")
def health() -> dict:
    inv = inventory()
    return {"status": "ok", "inventory_source": inv.name, "items": len(inv.list_items())}


@app.get("/api/items", response_model=list[Item])
def list_items(q: str | None = None, limit: int = 20) -> list[Item]:
    """Plain keyword filter on names and nicknames. The agent replaces this on Day 2."""
    items = inventory().list_items()
    if q:
        words = q.lower().split()
        items = [
            i for i in items
            if all(w in (i.name + " " + " ".join(i.nicknames) + " " + i.item_number).lower() for w in words)
        ]
    return items[:limit]


@app.get("/api/items/{item_id}", response_model=Item)
def get_item(item_id: str) -> Item:
    item = inventory().get_item(item_id)
    if not item:
        raise HTTPException(404, f"No item {item_id}")
    return item


@app.get("/api/items/{item_id}/stock", response_model=list[StockLevel])
def get_stock(item_id: str) -> list[StockLevel]:
    if not inventory().get_item(item_id):
        raise HTTPException(404, f"No item {item_id}")
    return inventory().get_stock(item_id)


@app.get("/api/locations", response_model=list[Location])
def list_locations() -> list[Location]:
    return inventory().list_locations()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")
