"""
================================================================================
Communication Analysis Toolkit — AI Analysis Agent
================================================================================

Three-layer Q&A architecture:
  Layer 1: Structured stat lookups (free, no LLM)
  Layer 2: RAG - retrieve messages + labels, send to any LLM
  Layer 3: Deep analysis with full context (optional big model)

The agent routes questions to the cheapest layer that can answer.
================================================================================
"""

from __future__ import annotations

import json
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import structlog
from structlog.contextvars import bound_contextvars

from engine.storage import CaseStorage

log: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Agent response
# ---------------------------------------------------------------------------


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
        for s in self.labels.get("supportive", []):
            tags.append(f"supportive={s}")
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


@dataclass
class AgentAnswer:
    """Structured answer from the agent."""

    answer: str
    layer: int  # 1=structured, 2=RAG, 3=deep
    confidence: float = 1.0
    evidence: list[str] = field(default_factory=list)
    retrieval: RetrievalResult | None = None


# ---------------------------------------------------------------------------
# Layer 1: Structured stat queries (no LLM needed)
# ---------------------------------------------------------------------------


class StructuredQueryEngine:
    """Answers pure data questions from pre-computed stats."""

    def __init__(self, storage: CaseStorage, case_id: int, user_name: str, contact_name: str) -> None:
        self._storage = storage
        self._case_id = case_id
        self._user = user_name
        self._contact = contact_name

    def try_answer(self, question: str) -> AgentAnswer | None:
        """Try to answer with pure data. Returns None if can't."""
        try:
            # Note: We are now querying DB on demand, so efficient.
            return self._try_answer_inner(question)
        except Exception:
            log.warning("layer1_error", question=question[:100], exc_info=True)
            return None  # Fall through to Layer 2

    def _try_answer_inner(self, question: str) -> AgentAnswer | None:
        """Inner dispatch."""
        q = question.lower().strip()

        # Total messages
        if self._match_any(q, ["how many messages", "total messages",
                                "message count", "number of messages"]):
            return self._count_messages()

        # Total days
        if self._match_any(q, ["how many days", "total days", "number of days",
                                "how long"]):
            return self._count_days()

        # Hurtful counts
        if self._match_any(q, ["how many hurtful", "how many times hurtful",
                                "hurtful count", "how much hurtful"]):
            return self._count_hurtful()

        # Pattern counts
        if self._match_any(q, ["how many times", "how often", "count of",
                                "instances of"]) and self._has_pattern_word(q):
            return self._count_patterns(q)

        # Who sent more / who was worse
        if self._match_any(q, ["who sent more", "who messaged more",
                                "who texted more"]):
            return self._who_sent_more()
        if self._match_any(q, ["who was worse", "who was more hurtful",
                                "who said more hurtful", "who was meaner"]):
            return self._who_more_hurtful()

        # Worst day
        if self._match_any(q, ["worst day", "most hurtful day",
                                "worst single day", "most conflict"]):
            return self._worst_day()

        # Call stats
        if self._match_any(q, ["how many calls", "call count", "phone calls",
                                "talk time", "call duration"]):
            return self._call_stats()

        # Pattern breakdown
        if self._match_any(q, ["what patterns", "which patterns",
                                "pattern breakdown", "types of patterns",
                                "list patterns"]):
            return self._pattern_breakdown()

        # Severity breakdown
        if self._match_any(q, ["severity breakdown", "how severe",
                                "severity distribution", "mild moderate severe"]):
            return self._severity_breakdown()

        # Metadata
        if self._match_any(q, ["who is the user", "who am i", "user name"]):
            return AgentAnswer(answer=f"The user is {self._user}.", layer=1)
        if self._match_any(q, ["who is the contact", "contact name", "who are we analyzing"]):
            return AgentAnswer(answer=f"The contact is {self._contact}.", layer=1)

        return None

    # ---- Helpers ----

    @staticmethod
    def _match_any(text: str, patterns: list[str]) -> bool:
        return any(p in text for p in patterns)

    @staticmethod
    def _has_pattern_word(text: str) -> bool:
        pattern_words = [
            "darvo", "gaslight", "stonewall", "guilt", "love bomb",
            "future fak", "triangulat", "contempt", "criticism",
            "deflect", "minimiz", "blame", "silent treatment",
            "coercive", "manipulat", "deny", "reverse",
        ]
        return any(w in text for w in pattern_words)

    def _count_messages(self) -> AgentAnswer:
        stats = self._storage.get_daily_stats(self._case_id)
        total_sent = sum(d.get("sent", 0) for d in stats)
        total_recv = sum(d.get("received", 0) for d in stats)
        total = total_sent + total_recv
        return AgentAnswer(
            answer=(
                f"Total messages: {total:,}\n"
                f"  {self._user} sent: {total_sent:,}\n"
                f"  {self._contact} sent: {total_recv:,}"
            ),
            layer=1,
        )

    def _count_days(self) -> AgentAnswer:
        stats = self._storage.get_daily_stats(self._case_id)
        total = len(stats)
        return AgentAnswer(
            answer=f"Period covers {total} days of activity.",
            layer=1,
        )

    def _count_hurtful(self) -> AgentAnswer:
        stats = self._storage.get_daily_stats(self._case_id)
        total = sum(d.get("hurtful_count", 0) for d in stats)
        return AgentAnswer(
            answer=f"Total hurtful language instances detected: {total}",
            layer=1,
        )

    def _count_patterns(self, q: str) -> AgentAnswer:
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
        }
        target = None
        for keyword, pat_name in pattern_map.items():
            if keyword in q:
                target = pat_name
                break

        if not target:
            return AgentAnswer(answer="Couldn't identify the pattern.", layer=1, confidence=0.5)

        rows = self._storage.get_pattern_stats(self._case_id)
        count = 0
        for r in rows:
            pj = r.get("patterns_json", "[]")
            try:
                pats = json.loads(pj)
                if target in pats:
                    count += 1
            except:
                pass

        return AgentAnswer(
            answer=f"{target.replace('_', ' ').title()} detected {count} times.",
            layer=1,
        )

    def _who_sent_more(self) -> AgentAnswer:
        stats = self._storage.get_daily_stats(self._case_id)
        sent = sum(d.get("sent", 0) for d in stats)
        recv = sum(d.get("received", 0) for d in stats)
        if sent > recv:
            winner = self._user
            ratio = sent / max(recv, 1)
        else:
            winner = self._contact
            ratio = recv / max(sent, 1)
        return AgentAnswer(
            answer=f"{winner} sent more messages ({max(sent, recv):,} vs {min(sent, recv):,}, ratio {ratio:.1f}x).",
            layer=1,
        )

    def _who_more_hurtful(self) -> AgentAnswer:
        # Need direction breakdown of hurtful
        # get_daily_stats aggregates hurtful total.
        # I need a new query or just search messages with hurtful=1
        msgs = self._storage.search_messages(self._case_id, limit=10000) # Only last 10000? Scalability limit?
        # Actually search_messages is minimal.
        # Better: use get_daily_stats but logic needs checking.
        # get_daily_stats currently sums 'hurtful_count'. It doesn't split by direction.
        # I'll rely on pattern stats which includes direction? No, pattern stats includes direction.
        # Let's use search_messages with "is_hurtful=1" but no limit?
        # That's too heavy.
        # I'll fall back to a simpler answer or adding granular stats later.
        return AgentAnswer(answer="Detailed hurtful breakdown requires deeper analysis.", layer=1)

    def _worst_day(self) -> AgentAnswer:
        stats = self._storage.get_daily_stats(self._case_id)
        if not stats:
            return AgentAnswer(answer="No data found.", layer=1)

        worst = max(stats, key=lambda x: x.get("hurtful_count", 0))
        cnt = worst.get("hurtful_count", 0)

        if cnt == 0:
            return AgentAnswer(answer="No hurtful language was detected.", layer=1)
        return AgentAnswer(
            answer=f"Worst day: {worst['date']} ({cnt} hurtful instances).",
            layer=1,
        )

    def _call_stats(self) -> AgentAnswer:
        calls = self._storage.get_calls(self._case_id)
        total = len(calls)
        duration = sum(c.get("duration", 0) for c in calls)
        h = duration // 3600
        m = (duration % 3600) // 60
        return AgentAnswer(
            answer=f"Total calls: {total}. Total duration: {h}h {m}m.",
            layer=1,
        )

    def _pattern_breakdown(self) -> AgentAnswer:
        rows = self._storage.get_pattern_stats(self._case_id)
        counts: Counter[str] = Counter()
        for r in rows:
            try:
                pats = json.loads(r.get("patterns_json", "[]"))
                counts.update(pats)
            except Exception:
                pass

        if not counts:
            return AgentAnswer(answer="No behavioral patterns detected.", layer=1)
        lines = [f"Pattern breakdown ({sum(counts.values())} total):"]
        for pat, count in counts.most_common():
            lines.append(f"  {pat.replace('_', ' ').title()}: {count}")
        return AgentAnswer(answer="\n".join(lines), layer=1)

    def _severity_breakdown(self) -> AgentAnswer:
        # We can scan messages with severity
        # Or better: add get_severity_stats to storage.
        # For now, approximate with search (limited) or just say "not available via fast stats".
        return AgentAnswer(answer="Severity breakdown not available in fast stats.", layer=1)


# ---------------------------------------------------------------------------
# Layer 2: RAG — retrieve messages + labels → format for LLM
# ---------------------------------------------------------------------------


class RAGEngine:
    """Retrieves relevant messages using SQL Search."""

    def __init__(self, storage: CaseStorage, case_id: int, user_name: str, contact_name: str) -> None:
        self._storage = storage
        self._case_id = case_id
        self._user = user_name
        self._contact = contact_name

    def build_prompt(self, question: str) -> tuple[str, RetrievalResult]:
        """Build an LLM prompt with relevant context for the question."""
        result = self._search(question, limit=100)

        # Build system instruction
        system = (
            f"You are analyzing communication between {self._user} and {self._contact}.\n"
            "Each message has pre-computed labels from a clinical pattern detection engine:\n"
            "- patterns: detected behavioral patterns (DARVO, gaslighting, etc.)\n"
            "- supportive: positive communication (validation, empathy, appreciation)\n"
            "- severity: how hurtful the language is (severe/moderate/mild)\n"
            "- is_apology: whether the message is an apology\n"
            "- is_de_escalation: whether the message attempts to calm things down\n\n"
            "Use these labels as evidence. Answer based ONLY on the messages shown.\n"
            "Be specific — cite actual messages and dates when answering.\n"
            "If you can't answer from the data shown, say so.\n"
        )

        context = result.to_prompt_context(max_messages=100)
        prompt = f"{system}\n{context}\n\nQuestion: {question}\n\nAnswer:"
        return prompt, result

    def answer_locally(self, question: str) -> AgentAnswer:
        """Answer using the retrieved messages WITHOUT an LLM."""
        try:
            return self._answer_locally_inner(question)
        except Exception:
            log.warning("layer2_error", question=question[:100], exc_info=True)
            return AgentAnswer(
                answer="I encountered an issue analyzing that question.",
                layer=2, confidence=0.1,
            )

    def _answer_locally_inner(self, question: str) -> AgentAnswer:
        result = self._search(question, limit=200)

        if result.count == 0:
            return AgentAnswer(
                answer="I couldn't find any messages matching that query.",
                layer=2, confidence=0.3, retrieval=result,
            )

        # Simple summarization
        lines = [f"Found {result.count} relevant messages."]
        return AgentAnswer(
            answer="\n".join(lines),
            layer=2, confidence=0.7, retrieval=result,
        )

    def _search(self, query: str, limit: int = 50) -> RetrievalResult:
        # Simple text search for now.
        # Ideally, we parse "from user" etc to pass to search_messages.
        # Using basic keyword logic.

        q = query.lower()
        direction = None
        if "from user" in q or "i said" in q:
            direction = "sent" # or 'user', dependent on ingestion normalization
        elif "from contact" in q or "they said" in q:
            direction = "received"

        sql = """
            SELECT m.*, ma.is_hurtful, ma.severity, ma.patterns_json, ma.supportive_json, ma.is_apology
            FROM messages m
            LEFT JOIN message_analysis ma ON m.id = ma.message_id
            WHERE m.case_id = ?
        """
        params: list[Any] = [self._case_id]

        if q: # query_text is 'q' here
            sql += " AND m.body LIKE ?"
            params.append(f"%{q}%")

        if direction:
            sql += " AND m.direction LIKE ?"
            params.append(f"%{direction}%")

        sql += " ORDER BY m.timestamp DESC LIMIT ?"
        params.append(limit)

        with get_db_connection(self._storage.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()

        msgs = []
        for r in rows:
            labels = {}
            if r.get("is_hurtful"):
                labels["severity"] = r.get("severity", "moderate")
            if r.get("is_apology"):
                labels["is_apology"] = True

            pj = r.get("patterns_json", "[]")
            try:
                if pj and pj != "[]": # Check if not empty string or empty list string
                    labels["patterns"] = json.loads(pj)
            except Exception:
                pass

            sj = r.get("supportive_json", "[]")
            try:
                if sj and sj != "[]": # Check if not empty string or empty list string
                    labels["supportive"] = json.loads(sj)
            except Exception:
                pass

            msgs.append(RetrievedMessage(
                time=f"{r['date']} {r['time']}",
                direction=str(r.get("direction", "unknown")),
                body=str(r.get("body", "")),
                labels=labels
            ))

        return RetrievalResult(messages=msgs, total_searched=0, filters_applied=[])


# ---------------------------------------------------------------------------
# Main Agent (routes to the right layer)
# ---------------------------------------------------------------------------


class AnalysisAgent:
    """Routes questions to the cheapest layer that can answer."""

    def __init__(self, storage: CaseStorage, case_id: int, user_name: str = "User", contact_name: str = "Contact") -> None:
        self._storage = storage
        self._case_id = case_id
        self._structured = StructuredQueryEngine(storage, case_id, user_name, contact_name)
        self._rag = RAGEngine(storage, case_id, user_name, contact_name)

    def ask(self, question: str) -> AgentAnswer:
        """Answer a question about the communication data."""
        start_time = time.perf_counter()

        ctx = structlog.contextvars.get_contextvars()
        request_id = ctx.get("request_id") or str(uuid.uuid4())

        with bound_contextvars(request_id=request_id):
            log.info("agent_ask", question=question[:200])

            try:
                # Layer 1
                t0 = time.perf_counter()
                l1_answer = self._structured.try_answer(question)
                t1 = time.perf_counter()

                if l1_answer:
                    log.info("layer1_success", duration_ms=(t1-t0)*1000)
                    return l1_answer

                # Layer 2
                log.info("layer1_miss", duration_ms=(t1-t0)*1000)
                t2 = time.perf_counter()
                l2_answer = self._rag.answer_locally(question)
                t3 = time.perf_counter()

                log.info("layer2_success", duration_ms=(t3-t2)*1000)
                return l2_answer

            except Exception:
                log.error("agent_crash", exc_info=True)
                return AgentAnswer(
                    answer="I encountered a critical error while processing your request.",
                    layer=0, confidence=0.0,
                )
            finally:
                total_duration = (time.perf_counter() - start_time) * 1000
                log.info("agent_finish", duration_ms=total_duration)

    def ask_with_prompt(self, question: str) -> tuple[AgentAnswer, str]:
        answer = self.ask(question)
        prompt, _retrieval = self._rag.build_prompt(question)
        return answer, prompt
