import json
from typing import Literal

from openai import OpenAI, OpenAIError
from pydantic import BaseModel

from app import config, openfda
from app.inventory.base import InventoryAdapter
from app.llm import get_client
from app.models import Item
from app.openfda import FdaDevice, FdaError
from app.search import search

MAX_STEPS = 6  # model calls per request, so a confused model can't loop forever

SYSTEM_PROMPT = """You help operating room nurses find surgical supplies in the hospital catalog.
Nurses type or speak item names, nicknames, brand names or misspellings.
Spoken requests may be misheard ("Bobby" for "bovie", "lap s" for "laps"),
so also try sound-alike names.

Rules:
- Always call find_item before answering. If results don't fit, search again with
  another term (a brand name, the generic name, or a corrected spelling).
- Then call answer exactly once.
- status "match": you are confident which item they mean. List the best first.
- status "clarify": several items fit and differ in something the nurse must choose
  (size, needle, length). List the options and ask one short question.
- If nothing in the catalog fits after at most 2 searches, call lookup_fda_devices
  with a short generic description (e.g. "laparotomy sponge x-ray detectable").
  - If a result has in_our_catalog, answer "match" with that item number.
  - Otherwise answer "not_in_catalog": say we don't stock it and ORMC can source it.
    Never say an FDA product is in stock here.
- status "not_found": nothing fits in the catalog or the FDA lookup.
- Only use item numbers returned by find_item or in_our_catalog.
- This is supply logistics only. Never give medical advice or suggest which item to use.
- Keep the message under 25 words."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_item",
            "description": "Search the catalog by name, nickname, brand, item number or MPN. "
            "Returns up to 8 candidates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "e.g. 'bovie' or 'vicryl 2-0'"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_fda_devices",
            "description": "Only when the catalog has nothing that fits: look up real products "
            "in the FDA device database by description. Returns maker, model number, whether "
            "it's still sold, recalls, and in_our_catalog if we stock the same model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Generic product words, e.g. 'kittner dissector'",
                    }
                },
                "required": ["description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "answer",
            "description": "Give the final answer to the nurse.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["match", "clarify", "not_in_catalog", "not_found"],
                    },
                    "item_numbers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Matching item numbers, best first, at most 5",
                    },
                    "message": {"type": "string", "description": "Short message or question"},
                },
                "required": ["status", "item_numbers", "message"],
            },
        },
    },
]


class AgentResult(BaseModel):
    status: Literal["match", "clarify", "not_in_catalog", "not_found", "fallback"]
    message: str
    items: list[Item]
    steps: int  # how many model calls were used
    fda_devices: list[FdaDevice] = []  # only for "not_in_catalog"


def find_item(inventory: InventoryAdapter, query: str) -> list[dict]:
    """The find_item tool: Day 1 search, trimmed to what the model needs."""
    return [
        {
            "item_number": r.item.item_number,
            "name": r.item.name,
            "nicknames": r.item.nicknames,
            "unit": r.item.unit,
            "in_stock": r.item.total_stock() > 0,
        }
        for r in search(inventory, query, limit=8)
    ]


def stocked_item_number(inventory: InventoryAdapter, model_number: str | None) -> str | None:
    """Our item number if we stock this exact model (its MPN matches), else None."""
    if not model_number:
        return None
    for r in search(inventory, model_number, limit=1):
        if (r.item.mpn or "").lower() == model_number.lower():
            return r.item.item_number
    return None


def lookup_fda_devices(
    inventory: InventoryAdapter, description: str, fda_search
) -> tuple[list[FdaDevice], list[dict] | dict]:
    """The lookup_fda_devices tool. Returns the devices (kept for the nurse's screen)
    and a short version for the model."""
    try:
        devices = fda_search(description)
    except FdaError as error:
        return [], {"error": str(error)}
    summary = [
        {
            "brand": d.brand,
            "company": d.company,
            "model_number": d.model_number,
            "description": d.description,
            "still_sold": d.in_distribution,
            "recalls": len(d.recalls) if d.recalls_checked else "unknown",
            "in_our_catalog": stocked_item_number(inventory, d.model_number),
        }
        for d in devices
    ]
    return devices, summary


def fallback(inventory: InventoryAdapter, query: str, reason: str, steps: int = 0) -> AgentResult:
    """When the AI can't help, still show plain search results."""
    items = [r.item for r in search(inventory, query, limit=5)]
    return AgentResult(status="fallback", message=reason, items=items, steps=steps)


def build_answer(
    inventory: InventoryAdapter, query: str, args: dict, steps: int, fda_devices: list[FdaDevice]
) -> AgentResult:
    status = args.get("status")
    if status == "not_in_catalog":
        # Show the FDA devices our tool actually found, never ones the model describes
        if not fda_devices:
            return AgentResult(status="not_found", message="Not in our catalog.", items=[], steps=steps)
        return AgentResult(
            status=status, message=args.get("message", ""), items=[], steps=steps, fda_devices=fda_devices
        )
    # Never trust item numbers from the model: keep only ones that really exist
    items = [inventory.get_item(n) for n in args.get("item_numbers", [])[:5]]
    items = [item for item in items if item is not None]
    if status not in ("match", "clarify", "not_found"):
        return fallback(inventory, query, "Showing search results.", steps)
    if status != "not_found" and not items:
        return fallback(inventory, query, "Showing search results.", steps)
    return AgentResult(status=status, message=args.get("message", ""), items=items, steps=steps)


def run_agent(
    query: str,
    inventory: InventoryAdapter,
    client: OpenAI | None = None,
    model: str | None = None,
    fda_search=openfda.search_devices,  # tests pass a fake, so they never call the FDA
) -> AgentResult:
    fda_devices: list[FdaDevice] = []  # from the latest lookup_fda_devices call
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    try:
        client = client or get_client()
        for step in range(1, MAX_STEPS + 1):
            response = client.chat.completions.create(
                model=model or config.LLM_MODEL, messages=messages, tools=TOOLS
            )
            message = response.choices[0].message

            if not message.tool_calls:  # model replied in plain text: nudge it
                messages.append({"role": "assistant", "content": message.content or ""})
                messages.append({"role": "user", "content": "Use find_item, then answer."})
                continue

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in message.tool_calls
                    ],
                }
            )
            for call in message.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                if call.function.name == "answer":
                    return build_answer(inventory, query, args, step, fda_devices)
                if call.function.name == "find_item":
                    result = find_item(inventory, args.get("query", query))
                elif call.function.name == "lookup_fda_devices":
                    fda_devices, result = lookup_fda_devices(
                        inventory, args.get("description", query), fda_search
                    )
                else:
                    result = {"error": f"unknown tool {call.function.name}"}
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
                )
        return fallback(inventory, query, "Showing search results.", MAX_STEPS)
    except (OpenAIError, RuntimeError):
        return fallback(inventory, query, "AI assistant unavailable. Showing search results.")
