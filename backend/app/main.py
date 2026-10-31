import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from app.inventory.json_adapter import JsonAdapter
from app.models import Item, Location
from app.search import SearchResult, search

DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "data" / "catalog.json"
inventory = JsonAdapter(os.getenv("CATALOG_PATH", DEFAULT_CATALOG))

app = FastAPI(title="Surgical Item Finder")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items/search", response_model=list[SearchResult])
def search_items(
    q: str = Query(min_length=1, description="Name, nickname or item number"),
    limit: int = Query(10, ge=1, le=50),
):
    return search(inventory, q, limit)


@app.get("/items/{item_number}", response_model=Item)
def get_item(item_number: str):
    item = inventory.get_item(item_number)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_number} not found")
    return item


@app.get("/locations", response_model=list[Location])
def list_locations():
    return inventory.list_locations()
