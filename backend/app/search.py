from difflib import SequenceMatcher

from pydantic import BaseModel

from app.inventory.base import InventoryAdapter
from app.models import Item


class SearchResult(BaseModel):
    item: Item
    score: int     # 0-100, higher is a better match
    matched: str   # the name or nickname that matched


def _score(query: str, item: Item) -> tuple[int, str]:
    """How well one item matches the query. Score 0 means no match."""
    if query in (item.item_number.lower(), (item.mpn or "").lower()):
        return 100, item.item_number

    best = (0, "")
    for name in [item.name.lower(), *item.nicknames]:
        if query == name:
            score = 100                       # "bovie" == "bovie"
        elif name.startswith(query):
            score = 80                        # "bov" -> "bovie"
        elif query in name:
            score = 60                        # "laps" -> "small laps"
        elif all(word in name for word in query.split()):
            score = 50                        # "2-0 vicryl" -> "vicryl 2-0"
        else:
            similarity = SequenceMatcher(None, query, name).ratio()
            score = int(similarity * 50) if similarity >= 0.8 else 0  # typos
        if score > best[0]:
            best = (score, name)
    return best


def search(inventory: InventoryAdapter, query: str, limit: int = 10) -> list[SearchResult]:
    """Find items by name, nickname, item number or MPN, best matches first."""
    q = " ".join(query.lower().split())   # lowercase, tidy spaces
    if not q:
        return []
    results = []
    for item in inventory.list_items():
        score, matched = _score(q, item)
        if score:
            results.append(SearchResult(item=item, score=score, matched=matched))
    results.sort(key=lambda r: (-r.score, r.item.name))
    return results[:limit]
