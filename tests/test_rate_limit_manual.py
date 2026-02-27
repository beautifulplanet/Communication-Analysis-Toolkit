"""Test: verify rate limiting returns 429."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth

from api.main import app

AUTH = HTTPBasicAuth("admin", "changeme")
client = TestClient(app)


def test_rate_limiting() -> None:
    """Hit /api/cases 70 times — should get 429 before 70."""
    for i in range(70):
        response = client.get("/api/cases", auth=AUTH)
        if response.status_code == 429:
            return
        assert response.status_code == 200, f"Unexpected {response.status_code} at request {i + 1}"
    pytest.fail("Did not hit rate limit after 70 requests")
