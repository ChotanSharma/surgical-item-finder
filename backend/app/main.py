import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field

from app.agent import AgentResult, run_agent
from app.inventory.json_adapter import JsonAdapter
from app.models import Item, Location
from app.search import SearchResult, search

DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "data" / "catalog.json"
inventory = JsonAdapter(os.getenv("CATALOG_PATH", DEFAULT_CATALOG))

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

app = FastAPI(title="Surgical Item Finder")

# Serve the built React app (frontend/dist), made by "npm run build"
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def home():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return HTMLResponse(
        "<h1>Surgical Item Finder</h1>"
        "<p>Frontend not built yet. Run: cd frontend && npm install && npm run build</p>"
    )

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


class AgentRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)


@app.post("/agent/find", response_model=AgentResult)
def agent_find(request: AgentRequest):
    return run_agent(request.query, inventory)
