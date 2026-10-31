import json

import pytest
from pydantic import ValidationError

from app.inventory.json_adapter import JsonAdapter


def test_unknown_stock_location_is_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({
        "locations": [{"id": "ORMC", "name": "OR Materials Core", "kind": "ormc"}],
        "items": [{
            "item_number": "SIF-1",
            "name": "Test Item",
            "category": "Test",
            "stock": [{"location_id": "OR-77", "quantity": 1}],
        }],
    }))
    with pytest.raises(ValidationError, match="OR-77"):
        JsonAdapter(path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        JsonAdapter(tmp_path / "nope.json")
