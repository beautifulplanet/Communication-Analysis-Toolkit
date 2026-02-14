"""
================================================================================
Communication Analysis Toolkit — Message Retriever
================================================================================

Retrieves relevant messages from DATA.json based on a query.
Supports date filtering, keyword search, pattern filtering, and
direction filtering.  Returns messages with their pre-computed labels
so the agent/LLM has all context needed to answer any question.
================================================================================
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

from api.data import CaseDataReader
from api.utils import extract_date_range

log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@dataclass
class RetrievedMessage:
    """A single message with its pre-computed labels."""

    time: str
    direction: str
    body: str
    labels: dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 1.0

    def to_prompt_line(self) -> str:
        """Format as a readable line for an LLM prompt."""
        arrow = self.direction.replace("user", "User").replace("contact", "Contact")
        tags = []
        if self.labels.get("severity"):
            tags.append(f"severity={self.labels['severity']}")
        for p in self.labels.get("patterns", []):
            tags.append(f"pattern={p}")
        if self.labels.get("is_apology"):
            tags.append("apology=true")
        if self.labels.get("is_de_escalation"):
            tags.append("de_escalation=true")
        tag_str = f"  [{', '.join(tags)}]" if tags else ""
        return f"[{self.time}] {arrow}: {self.body}{tag_str}"


@dataclass
class RetrievalResult:
    """Collection of retrieved messages with metadata."""

    messages: list[RetrievedMessage] = field(default_factory=list)
    total_searched: int = 0
    filters_applied: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.messages)

    def to_prompt_context(self, max_messages: int = 100) -> str:
        """Format all messages as LLM-readable context."""
        msgs = self.messages[:max_messages]
        lines = [m.to_prompt_line() for m in msgs]
        header = f"--- {len(msgs)} of {self.count} messages"
        if self.filters_applied:
            header += f" (filtered by: {', '.join(self.filters_applied)})"
        header += " ---"
        return header + "\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------


class MessageRetriever:
    """Retrieves messages from pre-loaded DATA.json structure."""

    def __init__(self, data: dict[str, Any] | CaseDataReader) -> None:
        if isinstance(data, CaseDataReader):
            self._data = data
        else:
            self._data = CaseDataReader(data)

        self._all_messages: list[RetrievedMessage] = []
        self._skipped: int = 0
        self._index()

    def _index(self) -> None:
        """Flatten all messages from all days into a searchable list.

        Malformed messages are skipped with a warning rather than
        crashing the entire index build.
        """
        for _date_str, day in self._data.iter_days():
            for msg in day.get("messages", []):
                try:
                    self._all_messages.append(RetrievedMessage(
                        time=str(msg.get("time", "")),
                        direction=str(msg.get("direction", "")),
                        body=str(msg.get("body", "")),
                        labels=msg.get("labels", {}) if isinstance(msg.get("labels"), dict) else {},
                    ))
                except Exception:
                    log.warning("skip_malformed_message", date=_date_str, exc_info=True)
                    self._skipped += 1
        if self._skipped:
            log.info("index_complete", total=len(self._all_messages), skipped=self._skipped)

    @property
    def total_messages(self) -> int:
        """Total number of messages indexed."""
        return len(self._all_messages)

    @property
    def user_label(self) -> str:
        """Name/Label of the main user."""
        return self._data.user_name

    @property
    def contact_label(self) -> str:
        """Name/Label of the contact."""
        return self._data.contact_name

    def retrieve(
        self,
        *,
        date_start: str | None = None,
        date_end: str | None = None,
        keywords: list[str] | None = None,
        patterns: list[str] | None = None,
        direction: str | None = None,
        severity: str | None = None,
        is_apology: bool | None = None,
        is_hurtful: bool | None = None,
        limit: int = 200,
    ) -> RetrievalResult:
        """
        Retrieve messages matching the given filters.

        Args:
            date_start: Start date (YYYY-MM-DD), inclusive.
            date_end: End date (YYYY-MM-DD), inclusive.
            keywords: Text substrings to search for in message body.
            patterns: Pattern labels to filter by (e.g., ["gaslighting"]).
            direction: "user" or "contact" to filter by sender.
            severity: Severity level to filter.
            is_apology: Filter for apology messages only.
            is_hurtful: Filter for messages with any severity label.
            limit: Max messages to return.
        """
        result = RetrievalResult(total_searched=len(self._all_messages))
        filtered = self._all_messages

        if date_start:
            # Message time is "YYYY-MM-DD HH:MM", lexical compare works
            filtered = [m for m in filtered if m.time >= date_start]
            result.filters_applied.append(f"from={date_start}")

        if date_end:
            # Include the full end date (up to 23:59)
            end_bound = date_end + " 23:59:59"
            filtered = [m for m in filtered if m.time <= end_bound]
            result.filters_applied.append(f"to={date_end}")

        if direction:
            d = direction.lower()
            filtered = [m for m in filtered if d in m.direction.lower()]
            result.filters_applied.append(f"direction={d}")

        if severity:
            filtered = [m for m in filtered
                        if (m.labels.get("severity") or "").lower() == severity.lower()]
            result.filters_applied.append(f"severity={severity}")

        if patterns:
            pat_set = {p.lower() for p in patterns}
            filtered = [m for m in filtered
                        if pat_set & {p.lower() for p in m.labels.get("patterns", [])}]
            result.filters_applied.append(f"patterns={','.join(patterns)}")

        if is_apology is not None:
            filtered = [m for m in filtered if m.labels.get("is_apology") == is_apology]
            result.filters_applied.append(f"is_apology={is_apology}")

        if is_hurtful is not None:
            if is_hurtful:
                filtered = [m for m in filtered if m.labels.get("severity") is not None]
            else:
                filtered = [m for m in filtered if m.labels.get("severity") is None]
            result.filters_applied.append(f"is_hurtful={is_hurtful}")

        if keywords:
            kw_lower = [k.lower() for k in keywords]
            filtered = [
                m for m in filtered
                if any(k in m.body.lower() for k in kw_lower)
            ]
            result.filters_applied.append(f"keywords={','.join(keywords)}")

        result.messages = filtered[:limit]
        return result

    def search(self, query: str, limit: int = 50) -> RetrievalResult:
        """
        Smart search: parse a natural-language-ish query into filters.
        Falls back to keyword search if no structured filters detected.
        """
        q = query.lower().strip()
        kwargs: dict[str, Any] = {"limit": limit}

        # 1. Date Detection (Sprint 8)
        # Try to guess default year from case data
        default_year = 2025
        start_str = self._data.period.get("start", "")
        if len(start_str) >= 4 and start_str[:4].isdigit():
            default_year = int(start_str[:4])

        date_range = extract_date_range(query, default_year=default_year)
        if date_range:
            kwargs["date_start"], kwargs["date_end"] = date_range

        # 2. Direction detection
        user_l = self.user_label.lower()
        contact_l = self.contact_label.lower()
        if any(w in q for w in [f"from {contact_l}", f"{contact_l} said",
                                f"{contact_l} sent", "she said", "he said",
                                "they said", "from contact"]):
            kwargs["direction"] = "contact"
        elif any(w in q for w in [f"from {user_l}", "i said", "i sent",
                                   "my messages", "from user"]):
            kwargs["direction"] = "user"

        # 3. Pattern detection
        pattern_map = {
            "darvo": "darvo", "gaslight": "gaslighting",
            "stonewall": "stonewalling", "guilt": "guilt_trip",
            "love bomb": "love_bombing", "future fak": "future_faking",
            "triangulat": "triangulation", "contempt": "gottman_contempt",
            "criticism": "gottman_criticism", "deflect": "deflection",
            "minimiz": "minimizing", "blame": "blame_shifting",
            "silent treatment": "silent_treatment_threat",
            "coercive": "coercive_control", "manipulat": "manipulation",
            "deny": "deny", "reverse": "reverse_victim",
            "bad guy": "darvo", # common phrase for DARVO/reverse victim
        }
        found_patterns = []
        matched_tokens = set()

        for keyword, pat_name in pattern_map.items():
            if keyword in q:
                found_patterns.append(pat_name)
                # Track tokens to exclude from keywords
                for t in keyword.split():
                     matched_tokens.add(t)

        if "manipulation" in q:
            found_patterns.extend(["gaslighting", "darvo", "guilt_trip", "deflection"])
            matched_tokens.add("manipulation")

        if found_patterns:
            kwargs["patterns"] = list(set(found_patterns))

        # 4. Apology detection
        if any(w in q for w in ["apolog", "sorry", "apology", "apologize"]):
            kwargs["is_apology"] = True

        # 5. Severity
        for sev in ["severe", "moderate", "mild"]:
            if sev in q:
                kwargs["severity"] = sev
                break

        # 6. Hurtful detection
        if any(w in q for w in ["hurtful", "mean", "cruel", "abusive", "toxic"]):
            kwargs["is_hurtful"] = True

        # 7. Fallback to keyword search if only dates or limit are set
        # Actually, if we have date/direction/patterns, we might NOT want keywords?
        # But if the user says "messages about money in june", we need keywords "money".
        # Parsing "about money" is hard without NLP.
        # We'll extract significant words that aren't stop words.

        stop_words = {
            "the", "a", "an", "is", "was", "were", "are", "be", "been",
            "do", "did", "does", "have", "has", "had", "will", "would",
            "could", "should", "can", "may", "might", "shall", "to",
            "of", "in", "for", "on", "at", "by", "with", "from",
            "and", "or", "but", "not", "no", "so", "if", "then",
            "that", "this", "what", "when", "where", "who", "how",
            "why", "all", "any", "each", "every", "some", "me", "my",
            "i", "you", "your", "he", "she", "they", "it", "we",
            "them", "her", "him", "about", "there", "just", "ever",
            "really", "actually", "show", "tell", "find", "get",
            "being", "messages", "message", "say", "said", "sent", "text", "texts",
            "june", "july", "august", "september", "october", "november", "december",
            "january", "february", "march", "april", # strip months if used
            "example", "examples", "like", "such", # filler words
        }
        # Add names to stop words so we don't filter by them as keywords
        stop_words.add(self.user_label.lower())
        stop_words.add(self.contact_label.lower())

        # Simplify: regex split
        words = [w for w in re.split(r"\W+", q) if w and w not in stop_words and len(w) > 2]

        # Don't use words if they are part of detected patterns or dates?
        # A bit risky. But "messages in june" -> "june" is in stop_words now.
        # Don't use words if they are part of detected patterns
        if found_patterns or matched_tokens:
            words = [w for w in words if w not in found_patterns and w not in matched_tokens]

        if words:
            kwargs["keywords"] = words[:5]

        return self.retrieve(**kwargs)
