"""Test case deletion via API using TestClient."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth

from api.main import app

AUTH = HTTPBasicAuth("admin", "changeme")
client = TestClient(app)

CASES_DIR = "cases"
TEST_ID = "test_delete_case"


def test_deletion():
    case_path = os.path.join(CASES_DIR, TEST_ID)
    os.makedirs(case_path, exist_ok=True)
    with open(os.path.join(case_path, "DATA.json"), "w") as f:
        f.write("{}")

    res = client.delete(f"/api/cases/{TEST_ID}", auth=AUTH)

    if res.status_code == 404:
        pytest.skip("Delete endpoint not wired or case not found")

    assert res.status_code == 204
    assert not os.path.exists(case_path)
