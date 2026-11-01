"""Ask the real Muse Spark agent. Uses API credit.

Usage:  python scripts/try_agent.py "bovie"
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.agent import run_agent  # noqa: E402
from app.main import inventory  # noqa: E402

query = " ".join(sys.argv[1:]) or "bovie"
start = time.time()
result = run_agent(query, inventory)

print(f"Query:   {query}")
print(f"Status:  {result.status}   ({result.steps} model calls, {time.time() - start:.1f}s)")
print(f"Message: {result.message}")
for item in result.items:
    print(f"  {item.item_number}  {item.name}  (stock {item.total_stock()})")
