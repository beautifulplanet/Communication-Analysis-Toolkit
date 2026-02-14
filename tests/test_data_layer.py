
from api.data import CaseDataReader


def test_case_reader_basics():
    data = {"user": "Alice", "contact": "Bob", "days": {"2025-01-01": {"msg": "hi"}}}
    reader = CaseDataReader(data)

    assert reader.user_name == "Alice"
    assert reader.contact_name == "Bob"

    days = list(reader.iter_days())
    assert len(days) == 1
    assert days[0][0] == "2025-01-01"
    assert days[0][1] == {"msg": "hi"}

def test_case_reader_malformed_days():
    """Test resilience against days not being a dict."""
    data = {"days": ["list", "instead", "of", "dict"]}
    reader = CaseDataReader(data)
    days = list(reader.iter_days())
    assert len(days) == 0

def test_case_reader_malformed_day_content():
    """Test iteration over mixed content."""
    data = {"days": {"2025-01-01": {"ok": True}, "2025-01-02": "bad_string"}}
    reader = CaseDataReader(data)
    # The iterator checks isinstance(day_data, dict)
    # My implementation:
    # for date_str, day_data in sorted(days.items()):
    #     if isinstance(day_data, dict):
    #         yield date_str, day_data

    # So "bad_string" should be skipped?
    # Let me check my implementation in previous step.
    # Yes: `if isinstance(day_data, dict): yield ...`

    days = list(reader.iter_days())
    assert len(days) == 1
    assert days[0][0] == "2025-01-01"
