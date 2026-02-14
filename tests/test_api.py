
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

# Use the sample case for testing
CASE_ID = "sample"

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    # Verify Trace ID middleware
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0

def test_list_cases():
    response = client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["cases"], list)
    # Check if sample case is present
    found = any(c["case_id"] == CASE_ID for c in data["cases"])
    if not found:
        pytest.skip("Sample case not found, skipping specific case tests")

def test_get_summary():
    response = client.get(f"/api/cases/{CASE_ID}/summary")
    if response.status_code == 404:
        pytest.skip("Sample case data not found")
    assert response.status_code == 200
    data = response.json()
    assert "total_messages_sent" in data
    assert "user_label" in data

def test_ask_question():
    response = client.post(
        f"/api/cases/{CASE_ID}/ask",
        json={"question": "How many messages?"}
    )
    if response.status_code == 404:
        pytest.skip("Sample case data not found")
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "confidence" in data
    # Answer should contain a number
    assert any(char.isdigit() for char in data["answer"])

def test_ask_question_missing_case():
    response = client.post(
        "/api/cases/nonexistent_case_id/ask",
        json={"question": "Hello?"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "404"
    assert "Case 'nonexistent_case_id' not found" in data["error"]["message"]
    assert "request_id" in data["error"]
    assert len(data["error"]["request_id"]) > 0
    # Header should match body
    assert response.headers["X-Request-ID"] == data["error"]["request_id"]
