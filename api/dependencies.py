from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import HTTPException

# Cases directory — relative to project root
CASES_DIR = Path(os.environ.get("CASES_DIR", "cases"))


def find_data_json(case_id: str) -> Path | None:
    """Locate DATA.json for a given case."""
    case_dir = (CASES_DIR / case_id).resolve()
    try:
        case_dir.relative_to(CASES_DIR.resolve())
    except ValueError:
        # Path traversal attempt
        return None

    if not case_dir.is_dir():
        return None
    # Check common locations
    for subpath in ["output/DATA.json", "DATA.json"]:
        candidate = case_dir / subpath
        if candidate.is_file():
            return candidate
    return None


def load_case_data(case_id: str) -> dict[str, Any]:
    """Load and return parsed DATA.json for a case.

    Raises HTTPException 404 if not found.
    """
    data_path = find_data_json(case_id)
    if data_path is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found or has no DATA.json")
    try:
        with open(data_path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
        return result
    except (json.JSONDecodeError, OSError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to load case data: {e!s}") from e


def get_db(case_id: str) -> Path:
    """Get the database path for a case (ensure it exists)."""
    # In this architecture, we use a single shared DB or per-case DB?
    # storage.py uses "cases.db" in the cases root.
    # We need to verify if the case exists in the DB.
    # For now, return the DB path.
    # storage.py: get_db_path() -> cases/cases.db
    # We should probably return a CaseStorage instance.
    from engine.storage import CaseStorage
    from engine.db import get_db_path
    db_path = get_db_path()
    if not db_path.exists():
         raise HTTPException(status_code=404, detail="Database not initialized")
    return db_path

