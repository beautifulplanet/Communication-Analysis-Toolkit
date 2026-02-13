"""
================================================================================
Communication Analysis Toolkit — API Schemas
================================================================================

Pydantic response models for type-safe API responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class MessageStats(BaseModel):
    sent: int = 0
    received: int = 0


class CallStats(BaseModel):
    incoming: int = 0
    outgoing: int = 0
    missed: int = 0
    talk_seconds: int = 0


class HurtfulItem(BaseModel):
    time: str = ""
    words: list[str] = Field(default_factory=list)
    severity: str = ""
    preview: str = ""
    source: str = ""


class PatternItem(BaseModel):
    time: str = ""
    pattern: str = ""
    matched: str = ""
    message: str = ""
    source: str = ""


class DaySummary(BaseModel):
    date: str
    weekday: str = ""
    had_contact: bool = False
    messages: MessageStats = Field(default_factory=MessageStats)
    calls: CallStats = Field(default_factory=lambda: CallStats())
    hurtful_from_user: list[HurtfulItem] = Field(default_factory=list)
    hurtful_from_contact: list[HurtfulItem] = Field(default_factory=list)
    patterns_from_user: list[PatternItem] = Field(default_factory=list)
    patterns_from_contact: list[PatternItem] = Field(default_factory=list)


class GapItem(BaseModel):
    start: str
    end: str
    days: int
    reason: str = ""


# ---------------------------------------------------------------------------
# Top-level response models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "3.1.0"


class CaseInfo(BaseModel):
    case_id: str
    case_name: str = ""
    user_label: str = ""
    contact_label: str = ""
    period_start: str = ""
    period_end: str = ""
    generated: str = ""
    total_days: int = 0
    has_data: bool = False


class CaseListResponse(BaseModel):
    cases: list[CaseInfo] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    case_name: str = ""
    user_label: str = ""
    contact_label: str = ""
    period: dict[str, str] = Field(default_factory=dict)
    generated: str = ""
    total_days: int = 0
    contact_days: int = 0
    no_contact_days: int = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_calls: int = 0
    total_talk_seconds: int = 0
    hurtful_from_user: int = 0
    hurtful_from_contact: int = 0
    severity_breakdown: dict[str, dict[str, int]] = Field(default_factory=dict)
    pattern_counts_user: dict[str, int] = Field(default_factory=dict)
    pattern_counts_contact: dict[str, int] = Field(default_factory=dict)


class TimelineResponse(BaseModel):
    days: list[DaySummary] = Field(default_factory=list)
    gaps: list[GapItem] = Field(default_factory=list)


class PatternDetail(BaseModel):
    pattern: str
    label: str = ""
    total_user: int = 0
    total_contact: int = 0
    instances: list[PatternItem] = Field(default_factory=list)


class PatternsResponse(BaseModel):
    patterns: list[PatternDetail] = Field(default_factory=list)


class HurtfulResponse(BaseModel):
    from_user: list[HurtfulItem] = Field(default_factory=list)
    from_contact: list[HurtfulItem] = Field(default_factory=list)
