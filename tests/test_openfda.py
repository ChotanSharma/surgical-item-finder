import pytest

from app import openfda
from app.openfda import FdaDevice, FdaError

# Shaped like real openFDA records, trimmed to the fields we use
SPONGE_BOX = {
    "brand_name": "AMD-RITMED",
    "company_name": "AMD Medicom Inc",
    "catalog_number": "1515",
    "device_description": "AMD-RITMED LAPAROTOMY SPONGE 4PLY X-RAY DETECTABLE 18 X 18 Inch",
    "commercial_distribution_status": "In Commercial Distribution",
}
SPONGE_CASE = {**SPONGE_BOX}  # the FDA lists the case size separately: same model
OLD_SPONGE = {
    "brand_name": "OldCo",
    "company_name": "OldCo Inc",
    "version_or_model_number": "OC-1",
    "device_description": "Laparotomy sponge",
    "commercial_distribution_status": "Not in Commercial Distribution",
}
RECALL = {"event_date_initiated": "2018-04-23", "recall_status": "Terminated", "reason_for_recall": "Mislabeled"}


@pytest.fixture(autouse=True)
def empty_cache(monkeypatch):
    """Every test starts with nothing cached."""
    monkeypatch.setattr(openfda, "_cache", {})


@pytest.fixture
def fake_fda(monkeypatch):
    """Replaces the network call. Records each (path, search) asked for."""
    calls = []
    answers = {"udi": [OLD_SPONGE, SPONGE_BOX, SPONGE_CASE], "recall": []}

    def fake_get(path, search, limit):
        calls.append((path, search))
        return answers[path]

    monkeypatch.setattr(openfda, "_get", fake_get)
    return calls, answers


def test_search_builds_an_and_query_from_words(fake_fda):
    calls, _ = fake_fda
    openfda.search_devices("lap sponge, x-ray")
    assert calls[0] == ("udi", "device_description:(lap AND sponge AND x AND ray)")


def test_duplicates_removed_and_still_sold_first(fake_fda):
    devices = openfda.search_devices("laparotomy sponge")
    assert [d.model_number for d in devices] == ["1515", "OC-1"]
    assert devices[0].in_distribution is True
    assert devices[1].in_distribution is False


def test_recalls_are_attached(fake_fda):
    calls, answers = fake_fda
    answers["recall"] = [RECALL]
    devices = openfda.search_devices("laparotomy sponge")
    assert devices[0].recalls[0].status == "Terminated"
    assert devices[0].recalls_checked is True
    assert ("recall", 'recalling_firm:"AMD" AND product_description:"1515"') in calls


def test_failed_recall_check_still_shows_devices(fake_fda, monkeypatch):
    def broken(device):
        raise FdaError("down")

    monkeypatch.setattr(openfda, "find_recalls", broken)
    devices = openfda.search_devices("laparotomy sponge")
    assert len(devices) == 2
    assert devices[0].recalls_checked is False  # so the screen won't claim "no recalls"


def test_empty_description_skips_the_network(fake_fda):
    calls, _ = fake_fda
    assert openfda.search_devices("  ,, ") == []
    assert calls == []


def test_no_model_number_means_no_recall_lookup(fake_fda):
    calls, _ = fake_fda
    device = FdaDevice(brand=None, company="X", model_number=None, description="d", in_distribution=True)
    assert openfda.find_recalls(device) == []
    assert calls == []


def test_404_means_nothing_found(monkeypatch):
    import urllib.error

    def not_found(*args, **kwargs):
        raise urllib.error.HTTPError("url", 404, "Not Found", {}, None)

    monkeypatch.setattr(openfda.urllib.request, "urlopen", not_found)
    assert openfda.search_devices("zzzz") == []


def test_network_error_raises_fda_error(monkeypatch):
    import urllib.error

    def offline(*args, **kwargs):
        raise urllib.error.URLError("no internet")

    monkeypatch.setattr(openfda.urllib.request, "urlopen", offline)
    with pytest.raises(FdaError):
        openfda.search_devices("bone wax")



def test_repeat_search_uses_the_cache(fake_fda):
    calls, _ = fake_fda
    first = openfda.search_devices("Laparotomy sponge")
    count = len(calls)
    again = openfda.search_devices("laparotomy  sponge!")  # same words, different typing
    assert again == first
    assert len(calls) == count  # no new FDA requests


def test_failed_search_is_not_cached(monkeypatch):
    import urllib.error

    def offline(*args, **kwargs):
        raise urllib.error.URLError("no internet")

    monkeypatch.setattr(openfda.urllib.request, "urlopen", offline)
    with pytest.raises(FdaError):
        openfda.search_devices("bone wax")
    assert openfda._cache == {}  # so the next try asks the FDA again
