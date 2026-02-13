"""
================================================================================
Communication Analysis Toolkit — Type Definitions
================================================================================

Common type aliases, TypedDicts, and protocols used across the engine to
ensure deep type safety and clean IDE support.
================================================================================
"""

from datetime import datetime
from typing import Any, TypedDict


class MessageDict(TypedDict):
    source: str
    timestamp: int
    datetime: datetime
    date: str
    time: str
    direction: str
    body: str
    type: str


class CallDict(TypedDict):
    source: str
    timestamp: int
    datetime: datetime
    date: str
    time: str
    direction: str
    duration: int
    type: str


class HurtfulEntry(TypedDict):
    time: str
    words: list[str]
    severity: str
    preview: str
    source: str


class PatternEntry(TypedDict):
    time: str
    pattern: str
    matched: str
    message: str
    source: str


class DayMessages(TypedDict):
    sent: int
    received: int
    all: list[MessageDict]


class DayCalls(TypedDict):
    incoming: int
    outgoing: int
    missed: int
    total_seconds: int


class DayHurtful(TypedDict):
    from_user: list[HurtfulEntry]
    from_contact: list[HurtfulEntry]


class DayPatterns(TypedDict):
    from_user: list[PatternEntry]
    from_contact: list[PatternEntry]


class DaySupportive(TypedDict):
    from_user: list[dict[str, Any]]
    from_contact: list[dict[str, Any]]


class DayData(TypedDict):
    date: str
    weekday: str
    had_contact: bool
    messages: DayMessages
    calls: DayCalls
    hurtful: DayHurtful
    patterns: DayPatterns
    supportive: DaySupportive


class GapData(TypedDict):
    start: str
    end: str
    days: int
    reason: str


class HurtfulEntryWithDate(HurtfulEntry):
    date: str


class PatternEntryWithDate(PatternEntry):
    date: str
