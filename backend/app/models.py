from typing import Literal

from pydantic import BaseModel, Field

LocationKind = Literal["or", "core", "ormc"]


class Location(BaseModel):
    """A place where supplies are stored."""

    id: str                 # e.g. "OR-03", "CORE-A", "ORMC"
    name: str               # e.g. "Operating Room 3"
    kind: LocationKind


class StockLevel(BaseModel):
    """How many of one item are at one location."""

    location_id: str
    quantity: int = Field(ge=0)


class Item(BaseModel):
    """One surgical supply item in the catalog."""

    item_number: str        # e.g. "SIF-10023"
    mpn: str | None = None    # manufacturer part number
    name: str               # official catalog name
    nicknames: list[str] = []   # names teams actually use: "bovie", "laps"
    category: str           # e.g. "Electrosurgery", "Sponges"
    unit: str = "each"      # each, box, pack
    image: str | None = None
    stock: list[StockLevel] = []

    def total_stock(self) -> int:
        return sum(s.quantity for s in self.stock)
