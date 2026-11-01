import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app import config  # noqa: E402
from app.llm import get_client  # noqa: E402

client = get_client()

print("Models available on your account:")
for model in client.models.list():
    print("  ", model.id)

reply = client.chat.completions.create(
    model=config.LLM_MODEL,
    messages=[{"role": "user", "content": "Reply with exactly: Llama is ready"}],
)
print(f"\n{config.LLM_MODEL} says: {reply.choices[0].message.content}")
