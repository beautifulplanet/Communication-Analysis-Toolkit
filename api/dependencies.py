from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from cachetools import TTLCache, cached  # type: ignore[import-untyped]
from fastapi import HTTPException

from api.config import get_settings
from api.schemas import CaseInfo
from engine.crypto import decrypt_data

# Cases directory — relative to project root
CASES_DIR = get_settings().cases_path


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


def get_case_path(case_id: str) -> Path | None:
    """Resolve and validate case directory path.

    Returns None if:
    - Path traversal detected
    - Directory does not exist
    """
    case_dir = (CASES_DIR / case_id).resolve()
    try:
        case_dir.relative_to(CASES_DIR.resolve())
    except ValueError:
        # Path traversal attempt
        return None

    if not case_dir.is_dir():
        return None

    return case_dir


# Cache up to 100 cases for 5 minutes to reduce disk I/O under load
_case_data_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=100, ttl=300)


@cached(_case_data_cache)
def load_case_data(case_id: str) -> dict[str, Any]:
    """Load and return parsed DATA.json for a case.

    Raises HTTPException 404 if not found.
    """
    data_path = find_data_json(case_id)
    if data_path is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found or has no DATA.json")
    try:
        # Read file as bytes
        with open(data_path, "rb") as f:
            file_bytes = f.read()

        # Decrypt (if encrypted)
        decrypted_bytes = decrypt_data(file_bytes)

        # Parse JSON
        result: dict[str, Any] = json.loads(decrypted_bytes)
        return result
    except (json.JSONDecodeError, OSError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to load case data: {e!s}") from e


# Cache the case list for 10 seconds (it's heavy)
_case_list_cache: TTLCache[str, list[CaseInfo]] = TTLCache(maxsize=1, ttl=10)

def _scan_cases_sync() -> list[CaseInfo]:
    """Scans the filesystem for cases (blocking I/O)."""
    if "all" in _case_list_cache:
        return _case_list_cache["all"]  # type: ignore[no-any-return, return-value]

    cases: list[CaseInfo] = []
    if not CASES_DIR.is_dir():
        return []

    # Sort by name for consistent order
    try:
        entries = sorted(e for e in CASES_DIR.iterdir() if e.is_dir())
    except OSError:
        return []

    for entry in entries:
        case_id = entry.name
        data_path = find_data_json(case_id)
        info = CaseInfo(case_id=case_id, has_data=data_path is not None)

        if data_path:
            try:
                # This open() and json.load() is the expensive part
                # Read bytes and decrypt (supports both plain and encrypted)
                with open(data_path, "rb") as f:
                    file_bytes = f.read()

                # Decrypt (transparentsly handles plaintext fallback)
                decrypted = decrypt_data(file_bytes)
                data = json.loads(decrypted)

                info.case_name = data.get("case", "")
                info.user_label = data.get("user", "")
                info.contact_label = data.get("contact", "")
                period = data.get("period", {})
                info.period_start = period.get("start", "")
                info.period_end = period.get("end", "")
                info.generated = data.get("generated", "")
                info.total_days = len(data.get("days", {}))
            except (json.JSONDecodeError, OSError):
                # corrupted file, skip metadata but list the case
                pass

        cases.append(info)

    _case_list_cache["all"] = cases
    return cases


async def get_case_list_async() -> list[CaseInfo]:
    """Async wrapper for the blocking case scan."""
    loop = asyncio.get_running_loop()
    # Run in default executor (Thread Pool)
    return await loop.run_in_executor(None, _scan_cases_sync)


def get_db(case_id: str) -> Path:
    """Get the database path for a case (ensure it exists)."""
    # In this architecture, we use a single shared DB or per-case DB?
    # storage.py uses "cases.db" in the cases root.
    # We need to verify if the case exists in the DB.
    # For now, return the DB path.
    from engine.db import get_db_path
    return get_db_path()
    # DB creation is handled by engine/storage.py

