from __future__ import annotations

from collections.abc import MutableMapping

import structlog
from fastapi import HTTPException

from api.agent import AnalysisAgent
from engine.db import get_db_path
from engine.storage import CaseStorage

log = structlog.get_logger()

# Global cache: case_id -> (mtime, Agent)
_AGENT_CACHE: MutableMapping[str, tuple[float, AnalysisAgent]] = {}


def get_case_agent(case_id: str) -> AnalysisAgent:
    """Get or create an AnalysisAgent for the given case.

    Uses CaseStorage (SQLite) instead of loading huge JSON files.
    """
    db_path = get_db_path()
    if not db_path.exists():
         raise HTTPException(status_code=404, detail="Analysis database not found")

    try:
        mtime = db_path.stat().st_mtime
    except OSError as e:
        raise HTTPException(status_code=500, detail="Could not access database") from e

    cached = _AGENT_CACHE.get(case_id)
    if cached:
        cached_mtime, agent = cached
        if cached_mtime == mtime:
            return agent
        log.info("cache_invalidated", case_id=case_id)

    # Load fresh from DB
    log.info("loading_agent_from_db", case_id=case_id)
    store = CaseStorage(db_path)

    # Try finding by name (legacy folder name) or UUID
    case_meta = store.get_case_by_name(case_id)
    if not case_meta:
        case_meta = store.get_case_by_uuid(case_id)

    if not case_meta:
        # If not in DB, it might be an old case that needs re-analysis
        raise HTTPException(
            status_code=404,
            detail=f"Case '{case_id}' not found in database. Please re-run analysis."
        )

    agent = AnalysisAgent(
        storage=store,
        case_id=case_meta["id"],
        user_name=case_meta.get("user_name", "User"),
        contact_name=case_meta.get("contact_name", "Contact")
    )

    _AGENT_CACHE[case_id] = (mtime, agent)
    return agent
