import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
import sys

sys.path.append("apps/api")
from agents.supervisor.graph import _parse_query_params

queries = [
    "give me two email from devfolio",
    "give me last 4 hour all email",
    "give me 5 emails from Google",
    "show 1 email from Microsoft"
]

for q in queries:
    g_q, t_delta, limit = _parse_query_params(q)
    print(f"QUERY: '{q}'")
    print(f"  -> Gmail query: '{g_q}'")
    print(f"  -> Time delta: {t_delta}")
    print(f"  -> Limit: {limit}\n")
