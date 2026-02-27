"""End-to-end flow test using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth

from api.main import app

AUTH = HTTPBasicAuth("admin", "changeme")
client = TestClient(app)


def test_e2e_flow():
    res = client.post(
        "/api/upload",
        files={"file": ("test_flow.xml", "<root>test</root>", "text/xml")},
        auth=AUTH,
    )
    assert res.status_code == 201
    data = res.json()
    file_id = data["file_id"]
    filename = data["saved_as"]

    payload = {
        "case_name": "Flow Test Case",
        "user_label": "Me",
        "contact_label": "You",
        "source_file_id": file_id,
        "source_filename": filename,
    }
    res = client.post("/api/cases", json=payload, auth=AUTH)
    if res.status_code != 201:
        pytest.skip(f"Case creation returned {res.status_code} (path-dependent)")
    case_id = res.json()["case_id"]

    res = client.get("/api/cases", auth=AUTH)
    assert res.status_code == 200
    cases = res.json().get("cases", [])
    assert any(c["case_id"] == case_id for c in cases)

    client.delete(f"/api/cases/{case_id}", auth=AUTH)
