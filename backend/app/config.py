import os

from dotenv import load_dotenv

load_dotenv()  # reads .env in the folder you start the app from

# Meta Model API (OpenAI-compatible). The key lives only in .env, never in code.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.meta.ai/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "muse-spark-1.3")
