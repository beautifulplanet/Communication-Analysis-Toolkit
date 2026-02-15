"""Manual test: verify rate limiting returns 429."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_rate_limiting() -> None:
    """Hit /api/cases 70 times — should get 429 before 70."""
    print("Testing rate limit on /api/cases (limit: 60/min)...")
    for i in range(70):
        response = client.get("/api/cases")
        if response.status_code == 429:
            print(f"SUCCESS: Hit rate limit at request {i + 1}")
            return
        if response.status_code != 200:
            print(f"ERROR: Unexpected status {response.status_code} at request {i + 1}")
            return
    print("FAILURE: Did not hit rate limit after 70 requests")


if __name__ == "__main__":
    test_rate_limiting()
