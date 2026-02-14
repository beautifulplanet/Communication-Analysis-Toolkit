"""
================================================================================
Communication Analysis Toolkit — Agent Exceptions
================================================================================

Custom exception hierarchy for graceful error handling.
The agent should NEVER crash — it should degrade gracefully and explain
what went wrong in human-readable terms.
================================================================================
"""

from __future__ import annotations


class AgentError(Exception):
    """Base exception for all agent errors."""

    def __init__(self, message: str, *, recoverable: bool = True) -> None:
        self.message = message
        self.recoverable = recoverable
        super().__init__(message)


class DataFormatError(AgentError):
    """Raised when DATA.json has unexpected structure."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"Data format issue: {detail}",
            recoverable=True,
        )


class QueryParseError(AgentError):
    """Raised when a user question can't be understood."""

    def __init__(self, question: str) -> None:
        super().__init__(
            f"Couldn't parse the question: {question!r}",
            recoverable=True,
        )


class RetrievalError(AgentError):
    """Raised when message retrieval fails."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"Retrieval error: {detail}",
            recoverable=True,
        )
