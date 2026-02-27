"""Text paste upload endpoint tests using FastAPI TestClient."""

from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth

from api.main import app

AUTH = HTTPBasicAuth("admin", "changeme")
client = TestClient(app)


def test_text_upload():
    payload = {
        "content": "Assuming this is a chat log\nMe: Hello\nYou: Hi",
        "filename": "mypaste.txt",
    }
    res = client.post("/api/upload/text", json=payload, auth=AUTH)
    assert res.status_code == 201
    data = res.json()
    assert "file_id" in data


def test_bad_ext():
    payload = {"content": "exe content", "filename": "malware.exe"}
    res = client.post("/api/upload/text", json=payload, auth=AUTH)
    assert res.status_code == 400
