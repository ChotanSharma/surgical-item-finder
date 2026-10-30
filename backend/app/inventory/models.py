"""Standard inventory records. Every adapter returns these, whatever the source system."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class LocationType(str, Enum):
    OR = "or"          # supply cart inside an operating room
    CORE = "core"      # inventory core shared by a group of ORs
    ORMC = "ormc"      # OR Materials Core, the main supply room


class Item(BaseModel):
    id: str
    item_number: str
    name: str
    category: str
    nicknames: list[str] = Field(default_factory=list)
    unit: str = "each"
    image_url: str | None = None


class Location(BaseModel):
    id: str
    name: str
    type: LocationType
    x: float  # position on the floor plan, in meters
    y: float
    serves: list[str] = Field(default_factory=list)  # OR ids this core serves


class StockLevel(BaseModel):
    item_id: str
    location_id: str
    quantity: int
    bin: str | None = None
