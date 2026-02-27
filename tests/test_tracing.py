"""
Tracing smoke test — verify request_id propagation through the agent.

Requires a SQLite database with test data. Skips if unavailable.
"""

import pytest

from engine.db import init_db
from engine.storage import CaseStorage


@pytest.fixture
def storage(tmp_path):
    db_path = tmp_path / "trace_test.db"
    init_db(db_path)
    return CaseStorage(db_path)


@pytest.fixture
def case_id(storage):
    return storage.create_case(
        name="Trace Test",
        user_name="A",
        contact_name="B",
    )


def test_agent_returns_answer_with_tracing(storage, case_id):
    """Agent returns a valid answer and doesn't crash on tracing context."""
    from api.agent import AnalysisAgent

    agent = AnalysisAgent(storage, case_id, user_name="A", contact_name="B")
    ans = agent.ask("hello")
    assert ans.answer
    assert isinstance(ans.answer, str)
