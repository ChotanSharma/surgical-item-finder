from pathlib import Path

import pytest

from app.inventory.json_adapter import JsonAdapter

CATALOG = Path(__file__).resolve().parent.parent / "backend" / "data" / "catalog.json"


@pytest.fixture(scope="module")
def catalog():
    return JsonAdapter(CATALOG)


def test_catalog_size(catalog):
    assert len(catalog.list_items()) >= 250
    assert len(catalog.list_locations()) == 15


def test_item_numbers_are_unique(catalog):
    numbers = [item.item_number for item in catalog.list_items()]
    assert len(numbers) == len(set(numbers))


def test_every_item_has_a_nickname(catalog):
    assert all(item.nicknames for item in catalog.list_items())


@pytest.mark.parametrize("nickname", ["bovie", "laps", "kocher", "raytec", "yankauer"])
def test_common_nicknames_exist(catalog, nickname):
    matches = [i for i in catalog.list_items() if nickname in i.nicknames]
    assert matches, f"no item has the nickname '{nickname}'"
