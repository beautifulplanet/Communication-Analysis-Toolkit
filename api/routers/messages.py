from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_db
from engine.storage import CaseStorage

router = APIRouter()

@router.get("/cases/{case_id}/messages")
async def get_case_messages(
    case_id: str,
    limit: int = 50,
    offset: int = 0,
    date: Optional[str] = None,
    db_path: Path = Depends(get_db)  # noqa: B008
) -> list[dict[str, Any]]:
    """
    Get raw messages with pagination.

    - **limit**: Number of messages to return (max 100)
    - **offset**: Starting index
    - **date**: Filter by date (YYYY-MM-DD)
    """
    if limit > 100:
        limit = 100

    storage = CaseStorage(db_path)

    # Try finding by name (legacy folder name) or UUID
    case = storage.get_case_by_name(case_id)
    if not case:
        case = storage.get_case_by_uuid(case_id)

    if not case:
        raise HTTPException(status_code=404, detail="Case not found in database. Please run analysis first.")

    internal_id = case["id"]
    return storage.get_messages(internal_id, limit=limit, offset=offset, date_filter=date)
