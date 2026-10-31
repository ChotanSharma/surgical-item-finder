from pathlib import Path

from pydantic import BaseModel, model_validator

from app.inventory.memory_adapter import InMemoryAdapter
from app.models import Item, Location


class CatalogFile(BaseModel):
    """The shape of a catalog .json file."""

    locations: list[Location]
    items: list[Item]

    @model_validator(mode="after")
    def stock_locations_must_exist(self):
        known = {location.id for location in self.locations}
        for item in self.items:
            for stock in item.stock:
                if stock.location_id not in known:
                    raise ValueError(
                        f"{item.item_number} has stock at unknown location "
                        f"'{stock.location_id}'"
                    )
        return self


class JsonAdapter(InMemoryAdapter):
    """Loads the catalog from a JSON file, then works like InMemoryAdapter."""

    def __init__(self, path: str | Path):
        text = Path(path).read_text(encoding="utf-8")
        catalog = CatalogFile.model_validate_json(text)
        super().__init__(catalog.items, catalog.locations)
