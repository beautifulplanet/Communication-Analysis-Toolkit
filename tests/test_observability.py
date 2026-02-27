"""
Observability smoke tests — verify structured logging and layer routing.

Requires a SQLite database with test data. Skips if unavailable.
"""

import pytest

from engine.db import init_db
from engine.storage import CaseStorage


@pytest.fixture
def storage(tmp_path):
    db_path = tmp_path / "obs_test.db"
    init_db(db_path)
    return CaseStorage(db_path)


@pytest.fixture
def case_id(storage):
    return storage.create_case(
        name="Observability Test",
        user_name="A",
        contact_name="B",
    )


def test_agent_layer2_fallback(storage, case_id):
    """Layer 2 fallback: agent handles unknown questions without crashing."""
    from api.agent import AnalysisAgent

    agent = AnalysisAgent(storage, case_id, user_name="A", contact_name="B")
    ans = agent.ask("hello")
    assert ans.answer
    assert ans.layer == 2


def test_agent_layer1_structured(storage, case_id):
    """Layer 1: structured stat queries return numeric data."""
    from api.agent import AnalysisAgent

    agent = AnalysisAgent(storage, case_id, user_name="A", contact_name="B")
    ans = agent.ask("how many messages")
    assert ans.answer
    assert ans.layer == 1
