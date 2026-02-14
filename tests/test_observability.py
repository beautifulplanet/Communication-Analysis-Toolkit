
import logging

from api.agent import AnalysisAgent

# Configure logging to console
logging.basicConfig(level=logging.INFO)

print("Starting observability test...")
data = {"days": {}, "user": "A", "contact": "B", "period": {"start": "2025-01-01", "end": "2025-01-01"}}
agent = AnalysisAgent(data)

print("\n--- Test 1: L2 Fallback (Keyword Search) ---")
ans = agent.ask("hello")
# Should log: agent_answer_complete layer=2 duration_ms=... l1_time_ms=...

print("\n--- Test 2: L1 Exact Match ---")
# Need to mock L1 data?
# StructuredQueryEngine checks keywords. "how many messages"
ans = agent.ask("how many messages")
# Should log: agent_answer_complete layer=1 duration_ms=...

print("\nCheck logs above for duration_ms key.")
