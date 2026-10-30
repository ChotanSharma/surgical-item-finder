"""Picks the inventory adapter from settings, so switching systems needs no code changes.

INVENTORY_SOURCE = json | csv | sqlite
INVENTORY_PATH   = file or folder for that source
"""
from __future__ import annotations

import os
from pathlib import Path

from .base import InventoryAdapter
from .csv_adapter import CsvInventoryAdapter
from .json_adapter import JsonInventoryAdapter
from .sql_adapter import SqlInventoryAdapter

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PATH = REPO_ROOT / "data" / "catalog.json"


def build_adapter(source: str | None = None, path: str | None = None) -> InventoryAdapter:
    source = (source or os.getenv("INVENTORY_SOURCE", "json")).lower()
    path = path or os.getenv("INVENTORY_PATH") or str(DEFAULT_PATH)
    if source == "json":
        return JsonInventoryAdapter(path)
    if source == "csv":
        return CsvInventoryAdapter(path)
    if source == "sqlite":
        return SqlInventoryAdapter.sqlite(path)
    raise ValueError(f"Unknown INVENTORY_SOURCE '{source}'. Use json, csv or sqlite.")
