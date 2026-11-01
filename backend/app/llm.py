from openai import OpenAI

from app import config


def get_client() -> OpenAI:
    """Client for Meta's Llama API (or any host set in .env)."""
    if not config.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY is not set. Copy .env.example to .env and add your key.")
    return OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)

