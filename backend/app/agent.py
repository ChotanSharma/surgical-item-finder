import json
from typing import Literal

from openai import OpenAI, OpenAIError
from pydantic import BaseModel

from app import config
from app.inventory.base import InventoryAdapter
from app.llm import get_client
from app.models import Item
from app.search import search

MAX_STEPS = 4  # model calls per request, so a confused model can't loop forever

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
- status "not_found": nothing in the catalog fits.
- Only use item numbers returned by find_item.
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
            "name": "answer",
            "description": "Give the final answer to the nurse.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["match", "clarify", "not_found"]},
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
    status: Literal["match", "clarify", "not_found", "fallback"]
    message: str
    items: list[Item]
    steps: int  # how many model calls were used


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


def fallback(inventory: InventoryAdapter, query: str, reason: str, steps: int = 0) -> AgentResult:
    """When the AI can't help, still show plain search results."""
    items = [r.item for r in search(inventory, query, limit=5)]
    return AgentResult(status="fallback", message=reason, items=items, steps=steps)


def build_answer(inventory: InventoryAdapter, query: str, args: dict, steps: int) -> AgentResult:
    # Never trust item numbers from the model: keep only ones that really exist
    items = [inventory.get_item(n) for n in args.get("item_numbers", [])[:5]]
    items = [item for item in items if item is not None]
    status = args.get("status")
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
) -> AgentResult:
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
                    return build_answer(inventory, query, args, step)
                if call.function.name == "find_item":
                    result = find_item(inventory, args.get("query", query))
                else:
                    result = {"error": f"unknown tool {call.function.name}"}
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
                )
        return fallback(inventory, query, "Showing search results.", MAX_STEPS)
    except (OpenAIError, RuntimeError):
        return fallback(inventory, query, "AI assistant unavailable. Showing search results.")
