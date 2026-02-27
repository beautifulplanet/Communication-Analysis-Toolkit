"""Upload endpoint tests using FastAPI TestClient (no running server needed)."""

from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth

from api.main import app

AUTH = HTTPBasicAuth("admin", "changeme")
client = TestClient(app)


def test_upload_success():
    files = {"file": ("test.xml", "<root>content</root>", "text/xml")}
    res = client.post("/api/upload", files=files, auth=AUTH)
    assert res.status_code == 201
    data = res.json()
    assert "file_id" in data
    assert "saved_as" in data


def test_upload_invalid_ext():
    files = {"file": ("malware.exe", "binarydata", "application/octet-stream")}
    res = client.post("/api/upload", files=files, auth=AUTH)
    assert res.status_code == 400


def test_upload_large_check():
    files = {"file": ("data.json", '{"key": "value"}', "application/json")}
    res = client.post("/api/upload", files=files, auth=AUTH)
    assert res.status_code == 201
    data = res.json()
    assert "file_id" in data
