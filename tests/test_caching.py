"""Test agent caching in api.services — verifies cache hits and mtime-based invalidation."""

from unittest.mock import MagicMock, patch

import pytest

from api.services import _AGENT_CACHE, get_case_agent


@pytest.fixture(autouse=True)
def clear_cache():
    _AGENT_CACHE.clear()
    yield
    _AGENT_CACHE.clear()


@patch("api.services.CaseStorage")
@patch("api.services.get_db_path")
def test_agent_caching(mock_get_db_path, mock_storage_cls):
    mock_db_path = MagicMock()
    mock_db_path.exists.return_value = True
    mock_db_path.stat.return_value.st_mtime = 1000.0
    mock_get_db_path.return_value = mock_db_path

    mock_store = MagicMock()
    mock_store.get_case_by_name.return_value = {
        "id": 1, "user_name": "A", "contact_name": "B",
    }
    mock_storage_cls.return_value = mock_store

    agent1 = get_case_agent("test_case")
    assert mock_storage_cls.call_count == 1

    agent2 = get_case_agent("test_case")
    assert mock_storage_cls.call_count == 1
    assert agent1 is agent2

    mock_db_path.stat.return_value.st_mtime = 2000.0
    agent3 = get_case_agent("test_case")
    assert mock_storage_cls.call_count == 2
    assert agent3 is not agent1
