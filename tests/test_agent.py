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
    return NS(id=call_id, type="function", function=NS(name=name, arguments=json.dumps(args)))


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



# ---- not in our catalog: FDA lookup ----

from app.openfda import FdaDevice, FdaError  # noqa: E402

KITTNER = FdaDevice(
    brand="Secto", company="Aspen Surgical", model_number="81-1001",
    description="Secto Dissector, Kittner, single use", in_distribution=True, recalls_checked=True,
)


def fake_fda(*devices):
    """Stands in for openfda.search_devices and records what it was asked."""
    asked = []

    def search_devices(description):
        asked.append(description)
        return list(devices)

    search_devices.asked = asked
    return search_devices


def test_not_in_catalog_shows_fda_devices(inventory):
    fda = fake_fda(KITTNER)
    client = FakeClient([
        reply(tool_call("c1", "find_item", {"query": "kittner"})),
        reply(tool_call("c2", "lookup_fda_devices", {"description": "kittner dissector"})),
        reply(tool_call("c3", "answer", {
            "status": "not_in_catalog", "item_numbers": [], "message": "We don't stock it.",
        })),
    ])
    result = agent.run_agent("kittner", inventory, client=client, model="test", fda_search=fda)
    assert result.status == "not_in_catalog"
    assert result.fda_devices == [KITTNER]
    assert result.items == []
    assert fda.asked == ["kittner dissector"]
    # the model saw a short summary, including "still_sold"
    tool_messages = [m for m in client.sent[2] if m["role"] == "tool"]
    assert '"still_sold": true' in tool_messages[-1]["content"]


def test_fda_model_we_stock_is_flagged(inventory):
    bovie_mpn = inventory.get_item(BOVIE_PENCIL).mpn
    same_model = KITTNER.model_copy(update={"model_number": bovie_mpn})
    devices, summary = agent.lookup_fda_devices(inventory, "pencil", fake_fda(same_model))
    assert summary[0]["in_our_catalog"] == BOVIE_PENCIL


def test_fda_error_is_told_to_the_model(inventory):
    def down(description):
        raise FdaError("FDA lookup unavailable")

    devices, summary = agent.lookup_fda_devices(inventory, "kittner", down)
    assert devices == []
    assert summary == {"error": "FDA lookup unavailable"}


def test_not_in_catalog_without_lookup_becomes_not_found(inventory):
    client = FakeClient([
        reply(tool_call("c1", "answer", {
            "status": "not_in_catalog", "item_numbers": [], "message": "Try Acme model X.",
        })),
    ])
    result = agent.run_agent("kittner", inventory, client=client, model="test", fda_search=fake_fda())
    assert result.status == "not_found"
    assert result.fda_devices == []
    assert "Acme" not in result.message  # the model's made-up product isn't shown



def test_not_found_without_fda_lookup_gets_one_anyway(inventory):
    fda = fake_fda(KITTNER)
    client = FakeClient([
        reply(tool_call("c1", "find_item", {"query": "kittner"})),
        reply(tool_call("c2", "answer", {"status": "not_found", "item_numbers": [], "message": "No."})),
    ])
    result = agent.run_agent("tourniquet cuff", inventory, client=client, model="test", fda_search=fda)
    assert result.status == "not_in_catalog"
    assert result.fda_devices == [KITTNER]
    assert fda.asked == ["tourniquet cuff"]  # the app searched with the nurse's words


def test_not_found_after_fda_lookup_is_kept(inventory):
    fda = fake_fda()  # FDA has nothing either
    client = FakeClient([
        reply(tool_call("c1", "lookup_fda_devices", {"description": "zzz"})),
        reply(tool_call("c2", "answer", {"status": "not_found", "item_numbers": [], "message": "Nothing."})),
    ])
    result = agent.run_agent("zzz", inventory, client=client, model="test", fda_search=fda)
    assert result.status == "not_found"
    assert fda.asked == ["zzz"]  # asked once, not twice
