import pytest

from app import config, llm


def test_missing_key_gives_clear_error(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        llm.get_client()


def test_client_uses_configured_host(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://example.com/v1")
    client = llm.get_client()
    assert str(client.base_url).startswith("https://example.com/v1")
