import copy
import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
from openai import OpenAIError

from app import agent, config
from app.inventory.json_adapter import JsonAdapter

CATALOG = Path(__file__).resolve().parent.parent / "backend" / "data" / "catalog.json"
BOVIE_PENCIL = "SIF-10107"
VICRYL_2_0_CT1 = "SIF-10003"
VICRYL_2_0_SH = "SIF-10004"


@pytest.fixture(scope="module")
def inventory():
    return JsonAdapter(CATALOG)


# ---- a fake model client, so tests are free, fast and work offline ----

def tool_call(call_id, name, args):
    return NS(id=call_id, function=NS(name=name, arguments=json.dumps(args)))


def reply(*calls, content=None):
    return NS(choices=[NS(message=NS(content=content, tool_calls=list(calls) or None))])


class FakeClient:
    """Plays back scripted model replies and records what it was sent."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []
        self.chat = NS(completions=NS(create=self.create))

    def create(self, **kwargs):
        self.sent.append(copy.deepcopy(kwargs["messages"]))
        return self.replies.pop(0)


class BrokenClient:
    """Acts like the API is down."""

    def __init__(self):
        self.chat = NS(completions=NS(create=self.create))

    def create(self, **kwargs):
        raise OpenAIError("API is down")


# ---- tests ----

def test_match_after_search(inventory):
    client = FakeClient([
        reply(tool_call("c1", "find_item", {"query": "bovie"})),
        reply(tool_call("c2", "answer", {
            "status": "match", "item_numbers": [BOVIE_PENCIL], "message": "Bovie pencil.",
        })),
    ])
    result = agent.run_agent("bovie", inventory, client=client, model="test")
    assert result.status == "match"
    assert result.items[0].item_number == BOVIE_PENCIL
    assert result.steps == 2
    # the model's second call included the search results from find_item
    tool_messages = [m for m in client.sent[1] if m["role"] == "tool"]
    assert "Electrosurgical Pencil" in tool_messages[0]["content"]


def test_clarify_returns_options(inventory):
    client = FakeClient([
        reply(tool_call("c1", "find_item", {"query": "vicryl 2-0"})),
        reply(tool_call("c2", "answer", {
            "status": "clarify",
            "item_numbers": [VICRYL_2_0_CT1, VICRYL_2_0_SH],
            "message": "CT-1 or SH needle?",
        })),
    ])
    result = agent.run_agent("vicryl 2-0", inventory, client=client, model="test")
    assert result.status == "clarify"
    assert [i.item_number for i in result.items] == [VICRYL_2_0_CT1, VICRYL_2_0_SH]


def test_made_up_item_numbers_are_dropped(inventory):
    client = FakeClient([
        reply(tool_call("c1", "answer", {
            "status": "match", "item_numbers": ["FAKE-1", BOVIE_PENCIL], "message": "ok",
        })),
    ])
    result = agent.run_agent("bovie", inventory, client=client, model="test")
    assert [i.item_number for i in result.items] == [BOVIE_PENCIL]


def test_only_made_up_items_falls_back_to_search(inventory):
    client = FakeClient([
        reply(tool_call("c1", "answer", {
            "status": "match", "item_numbers": ["FAKE-1"], "message": "ok",
        })),
    ])
    result = agent.run_agent("bovie", inventory, client=client, model="test")
    assert result.status == "fallback"
    assert result.items[0].item_number == BOVIE_PENCIL


def test_gives_up_after_max_steps(inventory):
    client = FakeClient(
        [reply(tool_call(f"c{i}", "find_item", {"query": "bovie"})) for i in range(agent.MAX_STEPS)]
    )
    result = agent.run_agent("bovie", inventory, client=client, model="test")
    assert result.status == "fallback"
    assert result.steps == agent.MAX_STEPS


def test_plain_text_reply_gets_a_nudge(inventory):
    client = FakeClient([
        reply(content="Let me think..."),
        reply(tool_call("c1", "answer", {
            "status": "match", "item_numbers": [BOVIE_PENCIL], "message": "ok",
        })),
    ])
    result = agent.run_agent("bovie", inventory, client=client, model="test")
    assert result.status == "match"
    assert client.sent[1][-1] == {"role": "user", "content": "Use find_item, then answer."}


def test_api_error_falls_back_to_search(inventory):
    result = agent.run_agent("bovie", inventory, client=BrokenClient(), model="test")
    assert result.status == "fallback"
    assert result.items[0].item_number == BOVIE_PENCIL


def test_missing_key_falls_back_to_search(inventory, monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    result = agent.run_agent("bovie", inventory)
    assert result.status == "fallback"
