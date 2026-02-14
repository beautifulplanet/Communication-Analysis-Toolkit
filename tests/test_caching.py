
from unittest.mock import MagicMock, patch

import pytest

from api.services import _AGENT_CACHE, get_case_agent

# Mock data content
MOCK_DATA = {"case": "Test", "days": {}}

@pytest.fixture(autouse=True)
def clear_cache():
    _AGENT_CACHE.clear()
    yield
    _AGENT_CACHE.clear()

@patch("api.services.find_data_json")
@patch("api.services.load_case_data")
def test_agent_caching(mock_load, mock_find):
    # Setup mock
    mock_path = MagicMock()
    mock_path.stat.return_value.st_mtime = 1000.0
    mock_find.return_value = mock_path
    mock_load.return_value = MOCK_DATA

    # 1. First call - should load
    agent1 = get_case_agent("test_case")
    assert mock_load.call_count == 1

    # 2. Second call - should be cached (same object)
    agent2 = get_case_agent("test_case")
    assert mock_load.call_count == 1
    assert agent1 is agent2

    # 3. Change mtime - should reload
    mock_path.stat.return_value.st_mtime = 2000.0
    agent3 = get_case_agent("test_case")
    assert mock_load.call_count == 2
    assert agent3 is not agent1
