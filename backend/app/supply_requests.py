from datetime import datetime, timezone
from threading import Lock
from typing import Literal

from pydantic import BaseModel, Field

from app.availability import check_stock
from app.inventory.base import InventoryAdapter

Fulfillment = Literal["ormc_delivery", "self_pick"]
Status = Literal["sent", "self_picked", "accepted", "delivered"]


class RequestLine(BaseModel):
    """One cart line, as the nurse's phone sends it."""

    item_number: str
    quantity: int = Field(ge=1, le=100)


class NewRequest(BaseModel):
    """What the phone sends when the nurse taps a submit button."""

    or_id: str = Field(pattern=r"^OR-\d{2}$")
    fulfillment: Fulfillment
    lines: list[RequestLine] = Field(min_length=1, max_length=20)


class PickLine(BaseModel):
    """One line of a saved request, with where to pick it from."""

    item_number: str
    name: str
    quantity: int
    pick_from: str | None       # location id, None if nowhere has enough
    pick_from_name: str | None


class SupplyRequest(BaseModel):
    id: int
    or_id: str
    fulfillment: Fulfillment
    status: Status
    created_at: datetime
    lines: list[PickLine]


class UnknownItemError(ValueError):
    pass


class RequestStore:
    """Keeps every request in memory. Every cart is recorded, delivered or
    self-picked, so usage history builds up for later supply insights."""

    def __init__(self, inventory: InventoryAdapter):
        self.inventory = inventory
        self._requests: list[SupplyRequest] = []
        self._lock = Lock()  # two nurses submitting at once can't get the same id

    def create(self, new: NewRequest) -> SupplyRequest:
        lines = []
        for line in new.lines:
            item = self.inventory.get_item(line.item_number)
            if item is None:
                raise UnknownItemError(line.item_number)
            places = [p for p in check_stock(self.inventory, item, new.or_id, line.quantity) if p.enough]
            best = places[0].location if places else None
            lines.append(
                PickLine(
                    item_number=item.item_number,
                    name=item.name,
                    quantity=line.quantity,
                    pick_from=best.id if best else None,
                    pick_from_name=best.name if best else None,
                )
            )
        with self._lock:
            request = SupplyRequest(
                id=len(self._requests) + 1,
                or_id=new.or_id,
                fulfillment=new.fulfillment,
                status="sent" if new.fulfillment == "ormc_delivery" else "self_picked",
                created_at=datetime.now(timezone.utc),
                lines=lines,
            )
            self._requests.append(request)
        return request

    def list(self) -> list[SupplyRequest]:
        return list(reversed(self._requests))  # newest first

    def get(self, request_id: int) -> SupplyRequest | None:
        if 1 <= request_id <= len(self._requests):
            return self._requests[request_id - 1]
        return None
