"""
================================================================================
Test Suite: Malformed Data Resilience
================================================================================

Verifies that the Agent and Retriever degrade gracefully when encountering
empty or edge-case data. The agent should NEVER crash; it should return
whatever valid information remains, or a polite fallback message.

These tests use the new CaseStorage-backed AnalysisAgent. Malformed dict
structures are tested at the ingestion layer, not the agent layer.
================================================================================
"""

from pathlib import Path

from api.agent import AnalysisAgent
from engine.db import init_db
from engine.storage import CaseStorage


def _make_agent(tmp_path: Path, name: str = "Malformed") -> AnalysisAgent:
    """Create a minimal agent backed by an empty SQLite DB."""
    db_path = tmp_path / f"{name}.db"
    init_db(db_path)
    storage = CaseStorage(db_path)
    case_id = storage.create_case(name=name, user_name="A", contact_name="B")
    return AnalysisAgent(storage, case_id, user_name="A", contact_name="B")


class TestRetrieverResilience:
    """Test that the agent handles empty/minimal data without crashing."""

    def test_skip_malformed_day(self, tmp_path: Path) -> None:
        """Agent handles a case with no messages at all."""
        agent = _make_agent(tmp_path, "Empty1")
        ans = agent.ask("test message")
        assert ans.answer

    def test_skip_malformed_message_list(self, tmp_path: Path) -> None:
        """Agent handles 'count messages' with zero messages."""
        agent = _make_agent(tmp_path, "Empty2")
        ans = agent.ask("count messages")
        assert ans.answer

    def test_skip_malformed_individual_message(self, tmp_path: Path) -> None:
        """Agent can query after inserting valid messages."""
        db_path = tmp_path / "ValidMsgs.db"
        init_db(db_path)
        storage = CaseStorage(db_path)
        case_id = storage.create_case(name="ValidMsgs", user_name="A", contact_name="B")

        storage.add_message(case_id, {
            "timestamp": 1000, "date": "2025-01-01", "time": "10:00",
            "source": "test", "direction": "sent", "body": "msg one",
        })
        storage.add_message(case_id, {
            "timestamp": 2000, "date": "2025-01-01", "time": "10:01",
            "source": "test", "direction": "received", "body": "msg two",
        })

        agent = AnalysisAgent(storage, case_id, user_name="A", contact_name="B")
        ans = agent.ask("How many messages total?")
        assert "2" in ans.answer

    def test_layer1_fallback_on_missing_keys(self, tmp_path: Path) -> None:
        """Layer 1 safely returns 0 for an empty case."""
        agent = _make_agent(tmp_path, "MissingKeys")
        ans = agent.ask("How many messages total?")
        assert "0" in ans.answer

    def test_total_garbage_input(self, tmp_path: Path) -> None:
        """Agent returns a valid answer even with zero data."""
        agent = _make_agent(tmp_path, "Garbage")
        ans = agent.ask("Anything happened?")
        assert ans.answer
        assert ans.layer

    def test_none_values_in_message(self, tmp_path: Path) -> None:
        """Agent handles edge-case message data without crashing."""
        db_path = tmp_path / "NoneVals.db"
        init_db(db_path)
        storage = CaseStorage(db_path)
        case_id = storage.create_case(name="NoneVals", user_name="A", contact_name="B")

        storage.add_message(case_id, {
            "timestamp": 0, "date": "2025-01-01", "time": "",
            "source": "test", "direction": "", "body": "content",
        })

        agent = AnalysisAgent(storage, case_id, user_name="A", contact_name="B")
        ans = agent.ask("How many messages total?")
        assert ans.answer
        assert ans.layer in (1, 2)
