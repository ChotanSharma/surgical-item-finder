import json
import sqlite3
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
    handled_by: str | None = None  # the ORMC associate who accepted it


class UnknownItemError(ValueError):
    pass


class RequestStore:
    """Saves every request in a SQLite database file. Every cart is recorded,
    delivered or self-picked, so usage history builds up for later supply insights."""

    def __init__(self, inventory: InventoryAdapter, db_path: str = ":memory:"):
        self.inventory = inventory
        # One shared connection; the lock stops two requests writing at the same moment
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row  # read columns by name: row["status"]
        self._lock = Lock()
        with self._lock, self._db:
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS requests (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    or_id       TEXT NOT NULL,
                    fulfillment TEXT NOT NULL,
                    status      TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    lines       TEXT NOT NULL  -- the pick lines, stored as JSON
                )"""
            )
            # Upgrade databases made before handled_by existed
            columns = [row["name"] for row in self._db.execute("PRAGMA table_info(requests)")]
            if "handled_by" not in columns:
                self._db.execute("ALTER TABLE requests ADD COLUMN handled_by TEXT")

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
        status = "sent" if new.fulfillment == "ormc_delivery" else "self_picked"
        created_at = datetime.now(timezone.utc)
        with self._lock, self._db:  # "with self._db" commits when the block ends
            cursor = self._db.execute(
                "INSERT INTO requests (or_id, fulfillment, status, created_at, lines) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    new.or_id,
                    new.fulfillment,
                    status,
                    created_at.isoformat(),
                    json.dumps([line.model_dump() for line in lines]),
                ),
            )
        return SupplyRequest(
            id=cursor.lastrowid,
            or_id=new.or_id,
            fulfillment=new.fulfillment,
            status=status,
            created_at=created_at,
            lines=lines,
        )

    def list(self, statuses: list[str] | None = None, limit: int = 100) -> list[SupplyRequest]:
        """Newest first, optionally only some statuses (e.g. ["sent", "accepted"])."""
        sql, params = "SELECT * FROM requests", []
        if statuses:
            sql += f" WHERE status IN ({', '.join('?' for _ in statuses)})"
            params += statuses
        sql += " ORDER BY id DESC LIMIT ?"
        with self._lock:
            rows = self._db.execute(sql, [*params, limit]).fetchall()
        return [self._to_request(row) for row in rows]

    def get(self, request_id: int) -> SupplyRequest | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
        return self._to_request(row) if row else None

    def accept(self, request_id: int, associate: str) -> SupplyRequest | None:
        """First associate to accept wins. None means it wasn't waiting any more."""
        return self._move(request_id, "sent", "accepted", associate)

    def deliver(self, request_id: int, associate: str) -> SupplyRequest | None:
        """Only the associate who accepted it can mark it delivered."""
        return self._move(request_id, "accepted", "delivered", associate)

    def _move(self, request_id: int, from_status: str, to_status: str, associate: str):
        # One UPDATE that also checks the current status, so two associates
        # tapping Accept at the same moment can't both win
        with self._lock, self._db:
            if from_status == "sent":
                cursor = self._db.execute(
                    "UPDATE requests SET status = ?, handled_by = ? WHERE id = ? AND status = ?",
                    (to_status, associate, request_id, from_status),
                )
            else:
                cursor = self._db.execute(
                    "UPDATE requests SET status = ? WHERE id = ? AND status = ? AND handled_by = ?",
                    (to_status, request_id, from_status, associate),
                )
        return self.get(request_id) if cursor.rowcount == 1 else None

    @staticmethod
    def _to_request(row: sqlite3.Row) -> SupplyRequest:
        return SupplyRequest(
            id=row["id"],
            or_id=row["or_id"],
            fulfillment=row["fulfillment"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            lines=json.loads(row["lines"]),
            handled_by=row["handled_by"],
    )
