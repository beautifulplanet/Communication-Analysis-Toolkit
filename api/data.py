"""
================================================================================
Communication Analysis Toolkit — Data Access Layer
================================================================================

Abstracts the raw DATA.json dictionary into a strongly-typed reader.
This allows the rest of the application to ignore the underlying JSON structure.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


class CaseDataReader:
    """Read-only access to the parsed case data."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize with loaded JSON data."""
        self._data = data

    @property
    def user_name(self) -> str:
        """Name of the user (who requested analysis)."""
        return str(self._data.get("user", "User"))

    @property
    def contact_name(self) -> str:
        """Name of the other person in the chat."""
        return str(self._data.get("contact", "Contact"))

    @property
    def period(self) -> dict[str, str]:
        """Start and end dates of the analysis."""
        p = self._data.get("period", {})
        if isinstance(p, dict):
            return {str(k): str(v) for k, v in p.items()}
        return {}

    @property
    def days(self) -> dict[str, Any]:
        """Raw days dictionary. prefer iter_days() for iteration."""
        days = self._data.get("days", {})
        if isinstance(days, dict):
            return days
        return {}

    @property
    def gaps(self) -> list[dict[str, Any]]:
        """Communication gaps (silent treatments, etc)."""
        gaps = self._data.get("gaps", [])
        return gaps if isinstance(gaps, list) else []

    def iter_days(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Iterate over all days in chronological order.

        Yields:
            (date_string, day_data_dict)
        """
        days = self._data.get("days", {})
        if not isinstance(days, dict):
            return

        for date_str, day_data in sorted(days.items()):
            if isinstance(day_data, dict):
                yield date_str, day_data
