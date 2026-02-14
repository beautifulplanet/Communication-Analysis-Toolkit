import os

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engine.tasks import analyze_case_task

router = APIRouter()

class AnalyzeRequest(BaseModel):
    case_id: str

class TaskResponse(BaseModel):
    task_id: str
    status: str

@router.post("/analyze/{case_id}", response_model=TaskResponse)
async def trigger_analysis(case_id: str):
    """
    Trigger a background analysis for a specific case.
    The case config must exist at cases/{case_id}/config.json.
    """
    config_path = f"cases/{case_id}/config.json"
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Case config not found")

    task = analyze_case_task.delay(config_path)
    return {"task_id": task.id, "status": "pending"}

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    Check the status of a background analysis task.
    """
    task_result = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status
    }
