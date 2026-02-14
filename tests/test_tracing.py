
import logging

from api.agent import AnalysisAgent

# Configure logging to console if not already
logging.basicConfig(level=logging.INFO)

print("Starting trace test...")
data = {"days": {}, "user": "A", "contact": "B", "period": {"start": "2025-01-01", "end": "2025-01-01"}}
agent = AnalysisAgent(data)
ans = agent.ask("hello")
print(f"Answer: {ans.answer}")
print("Check logs above for request_id=...")
