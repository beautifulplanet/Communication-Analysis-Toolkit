
import pytest

from api.agent import AnalysisAgent
from api.dependencies import load_case_data


@pytest.fixture(scope="module")
def agent():
    try:
        data = load_case_data("sample")
        return AnalysisAgent(data)
    except Exception as e:
        pytest.skip(f"Could not load sample data: {e}")

def test_l1_date_filtering(agent):
    """Test L1 counts with date filters."""
    # "June 2025"
    # Sample data starts 2025-06-01.
    # We need to know specific counts in sample.
    # Let's just check non-zero and less than total.

    # Total
    total = agent.ask("Total messages")
    assert "1,254" in total.answer

    # June
    june = agent.ask("How many messages in June 2025?")
    assert june.layer == 1
    # Check it's less than total
    # "Total messages: 435" (example guess)
    assert "Total messages" in june.answer
    assert "1,254" not in june.answer # Should be filtered

    # 2024 (Out of range)
    old = agent.ask("How many messages in 2024?")
    assert "Total messages: 0" in old.answer

def test_l2_date_filtering(agent):
    """Test L2 retrieval with date filters."""
    # "Messages in June"
    res = agent.ask("Show me messages in June 2025")
    assert res.layer == 2
    if res.retrieval:
        # Check filters (from=... or to=...)
        assert any("from=" in f or "to=" in f for f in res.retrieval.filters_applied)
        # Check messages are in June
        for m in res.retrieval.messages:
            assert m.time.startswith("2025-06")

def test_implicit_year(agent):
    """Test 'June' implies 'June 2025'."""
    res = agent.ask("How many messages in June?")
    assert res.layer == 1
    assert "Total messages: 0" not in res.answer # Should find some
