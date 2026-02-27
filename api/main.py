"""
================================================================================
Communication Analysis Toolkit — FastAPI Backend
================================================================================

Serves analysis data from DATA.json to the React dashboard.

Run:
    uvicorn api.main:app --reload --port 8000

All endpoints are read-only. Data stays local.
================================================================================
"""

from __future__ import annotations

import os
import shutil
import stat
from collections import defaultdict
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from api.dependencies import get_case_list_async, get_case_path, load_case_data
from api.errors import (
    agent_exception_handler,
    global_exception_handler,
    http_exception_handler,
)
from api.exceptions import AgentError
from api.middleware import BasicAuthMiddleware, RequestIdMiddleware
from api.routers.cases import router as cases_router
from api.routers.chat import router as chat_router
from api.routers.health import router as health_router
from api.routers.ingestion import router as ingestion_router
from api.routers.messages import router as messages_router
from api.routers.upload import router as upload_router
from api.schemas import (
    CallStats,
    CaseListResponse,
    DaySummary,
    GapItem,
    HurtfulItem,
    HurtfulResponse,
    MessageStats,
    PatternDetail,
    PatternItem,
    PatternsResponse,
    SummaryResponse,
    TimelineResponse,
)

logger = structlog.get_logger(__name__)


def _remove_readonly(func, path, exc_info):
    """Callback for shutil.rmtree to handle read-only files (Windows)."""
    if func in (os.rmdir, os.remove, os.unlink) and exc_info[1].errno == 13:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise


app = FastAPI(
    title="Communication Analysis Toolkit",
    description="API serving communication analysis data for the React dashboard.",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(BasicAuthMiddleware)

app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(ingestion_router, prefix="/api", tags=["Ingestion"])
app.include_router(messages_router, prefix="/api", tags=["Messages"])
app.include_router(cases_router, prefix="/api", tags=["Cases"])
app.include_router(upload_router, prefix="/api", tags=["Ingestion"])
app.include_router(health_router, prefix="/api", tags=["Health"])

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(AgentError, agent_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, global_exception_handler)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/cases", response_model=CaseListResponse)
@limiter.limit("60/minute")
async def list_cases(request: Request) -> CaseListResponse:
    """List all available cases (async scan)."""
    cases = await get_case_list_async()
    return CaseListResponse(cases=cases)


@app.get("/api/cases/{case_id}/summary", response_model=SummaryResponse)
@limiter.limit("20/minute")
async def get_summary(case_id: str, request: Request) -> SummaryResponse:
    """Executive summary statistics for a case."""
    data = load_case_data(case_id)
    days_data: dict[str, Any] = data.get("days", {})

    total_sent = 0
    total_received = 0
    total_calls = 0
    total_talk = 0
    contact_days = 0
    hurtful_user = 0
    hurtful_contact = 0
    severity_user: dict[str, int] = defaultdict(int)
    severity_contact: dict[str, int] = defaultdict(int)
    pattern_counts_user: dict[str, int] = defaultdict(int)
    pattern_counts_contact: dict[str, int] = defaultdict(int)

    for day in days_data.values():
        total_sent += day.get("messages_sent", 0)
        total_received += day.get("messages_received", 0)
        total_calls += day.get("calls_in", 0) + day.get("calls_out", 0) + day.get("calls_missed", 0)
        total_talk += day.get("talk_seconds", 0)
        if day.get("had_contact", False):
            contact_days += 1

        for h in day.get("hurtful_from_user", []):
            hurtful_user += 1
            severity_user[h.get("severity", "unknown")] += 1
        for h in day.get("hurtful_from_contact", []):
            hurtful_contact += 1
            severity_contact[h.get("severity", "unknown")] += 1

        for p in day.get("patterns_from_user", []):
            pattern_counts_user[p.get("pattern", "unknown")] += 1
        for p in day.get("patterns_from_contact", []):
            pattern_counts_contact[p.get("pattern", "unknown")] += 1

    total_days = len(days_data)
    return SummaryResponse(
        case_name=data.get("case", ""),
        user_label=data.get("user", ""),
        contact_label=data.get("contact", ""),
        period=data.get("period", {}),
        generated=data.get("generated", ""),
        total_days=total_days,
        contact_days=contact_days,
        no_contact_days=total_days - contact_days,
        total_messages_sent=total_sent,
        total_messages_received=total_received,
        total_calls=total_calls,
        total_talk_seconds=total_talk,
        hurtful_from_user=hurtful_user,
        hurtful_from_contact=hurtful_contact,
        severity_breakdown={
            "user": dict(severity_user),
            "contact": dict(severity_contact),
        },
        pattern_counts_user=dict(pattern_counts_user),
        pattern_counts_contact=dict(pattern_counts_contact),
    )


@app.get("/api/cases/{case_id}/timeline", response_model=TimelineResponse)
@limiter.limit("20/minute")
async def get_timeline(case_id: str, request: Request) -> TimelineResponse:
    """Day-by-day timeline data."""
    data = load_case_data(case_id)
    days_data: dict[str, Any] = data.get("days", {})
    gaps_data: list[dict[str, Any]] = data.get("gaps", [])

    days: list[DaySummary] = []
    for date_str in sorted(days_data.keys()):
        day = days_data[date_str]
        days.append(DaySummary(
            date=date_str,
            weekday=day.get("weekday", ""),
            had_contact=day.get("had_contact", False),
            messages=MessageStats(
                sent=day.get("messages_sent", 0),
                received=day.get("messages_received", 0),
            ),
            calls=CallStats(
                incoming=day.get("calls_in", 0),
                outgoing=day.get("calls_out", 0),
                missed=day.get("calls_missed", 0),
                talk_seconds=day.get("talk_seconds", 0),
            ),
            hurtful_from_user=[HurtfulItem(**h) for h in day.get("hurtful_from_user", [])],
            hurtful_from_contact=[HurtfulItem(**h) for h in day.get("hurtful_from_contact", [])],
            patterns_from_user=[PatternItem(**p) for p in day.get("patterns_from_user", [])],
            patterns_from_contact=[PatternItem(**p) for p in day.get("patterns_from_contact", [])],
        ))

    gaps = [GapItem(**g) for g in gaps_data]
    return TimelineResponse(days=days, gaps=gaps)


@app.get("/api/cases/{case_id}/patterns", response_model=PatternsResponse)
@limiter.limit("20/minute")
async def get_patterns(case_id: str, request: Request) -> PatternsResponse:
    """Pattern breakdown for a case."""
    data = load_case_data(case_id)
    days_data: dict[str, Any] = data.get("days", {})

    # Aggregate by pattern type
    user_by_pattern: dict[str, list[PatternItem]] = defaultdict(list)
    contact_by_pattern: dict[str, list[PatternItem]] = defaultdict(list)

    for day in days_data.values():
        for p in day.get("patterns_from_user", []):
            user_by_pattern[p.get("pattern", "unknown")].append(PatternItem(**p))
        for p in day.get("patterns_from_contact", []):
            contact_by_pattern[p.get("pattern", "unknown")].append(PatternItem(**p))

    all_patterns = sorted(set(list(user_by_pattern.keys()) + list(contact_by_pattern.keys())))
    details: list[PatternDetail] = []
    for pat in all_patterns:
        details.append(PatternDetail(
            pattern=pat,
            total_user=len(user_by_pattern.get(pat, [])),
            total_contact=len(contact_by_pattern.get(pat, [])),
            instances=user_by_pattern.get(pat, []) + contact_by_pattern.get(pat, []),
        ))

    return PatternsResponse(patterns=details)


@app.get("/api/cases/{case_id}/hurtful", response_model=HurtfulResponse)
@limiter.limit("20/minute")
async def get_hurtful(case_id: str, request: Request) -> HurtfulResponse:
    """Hurtful language breakdown for a case."""
    data = load_case_data(case_id)
    days_data: dict[str, Any] = data.get("days", {})

    from_user: list[HurtfulItem] = []
    from_contact: list[HurtfulItem] = []

    for day in days_data.values():
        for h in day.get("hurtful_from_user", []):
            from_user.append(HurtfulItem(**h))
        for h in day.get("hurtful_from_contact", []):
            from_contact.append(HurtfulItem(**h))

    return HurtfulResponse(from_user=from_user, from_contact=from_contact)


@app.delete("/api/cases/{case_id}", status_code=204)
@limiter.limit("5/minute")
async def delete_case(case_id: str, request: Request):
    """Delete a case directory."""
    case_path = get_case_path(case_id)
    if not case_path:
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        shutil.rmtree(case_path, onerror=_remove_readonly)
    except OSError as e:
        logger.error(f"Failed to delete case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete case") from e

    return Response(status_code=204)


# Mount static files (Dashboard)
# This must be last to allow API routes to take precedence
app.mount("/", StaticFiles(directory="static", html=True), name="static")



