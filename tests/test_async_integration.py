from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@patch("api.routers.ingestion.analyze_case_task.delay")
@patch("os.path.exists")
def test_trigger_analysis_success(mock_exists, mock_delay):
    # Setup mocks
    mock_exists.return_value = True
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_delay.return_value = mock_task

    # Execute
    response = client.post("/api/analyze/test_case")

    # Verify
    assert response.status_code == 200
    assert response.json() == {"task_id": "test-task-id", "status": "pending"}
    mock_delay.assert_called_once_with("cases/test_case/config.json")

@patch("os.path.exists")
def test_trigger_analysis_not_found(mock_exists):
    # Setup mocks
    mock_exists.return_value = False

    # Execute
    response = client.post("/api/analyze/missing_case")

    # Verify
    assert response.status_code == 404

@patch("api.routers.ingestion.AsyncResult")
def test_get_task_status(mock_async_result):
    # Setup mocks
    mock_result = MagicMock()
    mock_result.status = "SUCCESS"
    mock_async_result.return_value = mock_result

    # Execute
    response = client.get("/api/tasks/test-task-id")

    # Verify
    assert response.status_code == 200
    assert response.json() == {"task_id": "test-task-id", "status": "SUCCESS"}
