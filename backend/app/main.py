import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field

from app.agent import AgentResult, run_agent
from app.availability import Availability, check_stock   
from app.inventory.json_adapter import JsonAdapter
from app.models import Item, Location
from app.search import SearchResult, search
from app.supply_requests import NewRequest, RequestStore, SupplyRequest, UnknownItemError

DEFAULT_CATALOG = Path(__file__).resolve().parent.parent / "data" / "catalog.json"
inventory = JsonAdapter(os.getenv("CATALOG_PATH", DEFAULT_CATALOG))
DEFAULT_REQUESTS_DB = Path(__file__).resolve().parent.parent / "data" / "requests.db"
request_store = RequestStore(inventory, os.getenv("REQUESTS_DB", str(DEFAULT_REQUESTS_DB)))


FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
ITEM_IMAGES = Path(__file__).resolve().parent.parent / "data" / "images"

app = FastAPI(title="Surgical Item Finder")
# Item photos made by scripts/generate_images.py, e.g. /images/SIF-10107.webp
ITEM_IMAGES.mkdir(parents=True, exist_ok=True)  # folder may not exist on a fresh clone
app.mount("/images", StaticFiles(directory=ITEM_IMAGES), name="images")

# Serve the built React app (frontend/dist), made by "npm run build"
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/", include_in_schema=False)
@app.get("/ormc", include_in_schema=False)  # same React app; it shows the ORMC screen
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

@app.get("/items/{item_number}/availability", response_model=list[Availability])
def item_availability(
    item_number: str,
    or_id: str = Query(pattern=r"^OR-\d{2}$", description="The nurse's OR, e.g. OR-03"),
    quantity: int = Query(1, ge=1, le=100),
):
    item = inventory.get_item(item_number)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_number} not found")
    if inventory.get_location(or_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown OR {or_id}")
    return check_stock(inventory, item, or_id, quantity)

@app.get("/locations", response_model=list[Location])
def list_locations():
    return inventory.list_locations()


class AgentRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)


@app.post("/agent/find", response_model=AgentResult)
def agent_find(request: AgentRequest):
    return run_agent(request.query, inventory)


@app.post("/requests", response_model=SupplyRequest, status_code=201)
def create_request(new: NewRequest):
    if inventory.get_location(new.or_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown OR {new.or_id}")
    try:
        return request_store.create(new)
    except UnknownItemError as error:
        raise HTTPException(status_code=404, detail=f"Item {error} not found")


@app.get("/requests", response_model=list[SupplyRequest])
def list_requests(status: list[str] | None = Query(None, description="e.g. ?status=sent&status=accepted")):
    return request_store.list(status)



class Associate(BaseModel):
    associate: str = Field(min_length=1, max_length=40)


@app.get("/requests/{request_id}", response_model=SupplyRequest)
def get_request(request_id: int):
    request = request_store.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    return request


@app.post("/requests/{request_id}/accept", response_model=SupplyRequest)
def accept_request(request_id: int, body: Associate):
    accepted = request_store.accept(request_id, body.associate)
    if accepted is None:
        raise_conflict(request_id, "accepted")
    return accepted


@app.post("/requests/{request_id}/deliver", response_model=SupplyRequest)
def deliver_request(request_id: int, body: Associate):
    delivered = request_store.deliver(request_id, body.associate)
    if delivered is None:
        raise_conflict(request_id, "delivered")
    return delivered


def raise_conflict(request_id: int, action: str):
    """Explain why an Accept or Delivered tap didn't work."""
    current = request_store.get(request_id)
    if current is None:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    who = f" by {current.handled_by}" if current.handled_by else ""
    raise HTTPException(
        status_code=409,
        detail=f"Can't mark as {action}: request {request_id} is already {current.status}{who}",
    )

