from pathlib import Path

import pytest

from app.inventory.json_adapter import JsonAdapter
from app.search import search

CATALOG = Path(__file__).resolve().parent.parent / "backend" / "data" / "catalog.json"


@pytest.fixture(scope="module")
def inventory():
    return JsonAdapter(CATALOG)


@pytest.mark.parametrize(
    "query, expected",
    [
        ("bovie", "Electrosurgical Pencil, Rocker Switch"),
        ("laps", "Laparotomy Sponge 18 x 18 in"),
        ("kocher", "Kocher Clamp, Straight"),
        ("yankaur", "Yankauer Suction Tip"),      # typo
        ("  BOVIE ", "Electrosurgical Pencil, Rocker Switch"),  # caps and spaces
    ],
)
def test_top_result(inventory, query, expected):
    assert search(inventory, query)[0].item.name == expected


def test_search_by_item_number(inventory):
    result = search(inventory, "SIF-10001")[0]
    assert result.item.item_number == "SIF-10001"
    assert result.score == 100


def test_no_match_returns_empty(inventory):
    assert search(inventory, "xyzzy") == []


def test_limit(inventory):
    assert len(search(inventory, "vicryl", limit=3)) == 3
