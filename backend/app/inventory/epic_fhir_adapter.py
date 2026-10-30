"""Template for connecting Epic (or any FHIR R4 server).

Not used by the demo. Supply items in FHIR are usually exposed as
SupplyDelivery, Device or InventoryItem resources depending on the vendor and
version, and access needs the hospital's own credentials and approval.
This class shows where each piece maps so a hospital IT team can finish it.
"""
from __future__ import annotations

from .base import InventoryAdapter
from .models import Item, Location, StockLevel


class EpicFhirInventoryAdapter(InventoryAdapter):
    name = "epic_fhir"

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def list_items(self) -> list[Item]:
        # GET {base_url}/InventoryItem  (or the vendor's supply catalog endpoint)
        # map: identifier -> item_number, name -> name, category -> category,
        #      synonyms / alternate names -> nicknames
        raise NotImplementedError("Connect to your FHIR supply catalog endpoint")

    def list_locations(self) -> list[Location]:
        # GET {base_url}/Location?type=...  map physical position to x, y
        raise NotImplementedError("Connect to your FHIR Location endpoint")

    def get_stock(self, item_id: str) -> list[StockLevel]:
        # GET {base_url}/InventoryReport?item=...  (or the vendor's par level API)
        raise NotImplementedError("Connect to your stock or par level endpoint")
