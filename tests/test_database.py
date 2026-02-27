import sqlite3
from pathlib import Path

import pytest

from engine.db import get_db_connection, init_db
from engine.storage import CaseStorage

# Use a temporary file for testing
TEST_DB = Path("test_cases.db")

@pytest.fixture
def db_path(tmp_path):
    """Fixture to create a fresh temporary database for each test."""
    p = tmp_path / "cases.db"
    init_db(p)
    return p

def test_init_db(db_path):
    """Test that the database is initialized with the correct schema."""
    assert db_path.exists()
    with get_db_connection(db_path) as conn:
        # Check tables exist
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        names = [t[0] for t in tables]
        assert "cases" in names
        assert "messages" in names
        assert "message_analysis" in names

def test_create_case(db_path):
    """Test creating a new case."""
    store = CaseStorage(db_path)
    case_id = store.create_case("Test Case", "Alice", "Bob")
    assert case_id == 1

    case = store.get_case(case_id)
    assert case["name"] == "Test Case"
    assert case["user_name"] == "Alice"
    assert case["contact_name"] == "Bob"

def test_add_message(db_path):
    """Test adding raw messages."""
    store = CaseStorage(db_path)
    case_id = store.create_case("Msg Case", "A", "B")

    msg_data = {
        "timestamp": 1700000000,
        "date": "2024-01-01",
        "time": "12:00",
        "source": "sms",
        "direction": "user->contact",
        "body": "Hello World",
        "media_type": "text"
    }

    msg_id = store.add_message(case_id, msg_data)
    assert msg_id == 1

    # Verify retrieval
    msgs = store.get_messages(case_id)
    assert len(msgs) == 1
    assert msgs[0]["body"] == "Hello World"
    assert msgs[0]["source"] == "sms"

def test_add_analysis(db_path):
    """Test adding analysis results to a message."""
    store = CaseStorage(db_path)
    case_id = store.create_case("Analysis Case", "A", "B")
    msg_id = store.add_message(case_id, {"body": "test"})

    analysis = {
        "is_hurtful": True,
        "severity": "mild",
        "patterns": ["gaslighting"],
        "keywords": ["crazy"]
    }

    store.add_analysis(msg_id, analysis)

    # Verify directly in DB
    with get_db_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM message_analysis WHERE message_id = ?", (msg_id,)).fetchone()
        assert row["is_hurtful"] == 1
        assert "gaslighting" in row["patterns_json"]

def test_foreign_key_constraint(db_path):
    """Ensure messages cannot be added to non-existent cases."""
    store = CaseStorage(db_path)
    # Try adding to case_id 999 (does not exist)
    with pytest.raises(sqlite3.IntegrityError):
        store.add_message(999, {"body": "fail"})
