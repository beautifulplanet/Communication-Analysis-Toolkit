import json
import uuid
from pathlib import Path
from typing import Any, Optional

from engine.db import get_db_connection
from engine.types import MessageDict


class CaseStorage:
    """
    Data Access Object (DAO) for forensic case data.
    Abstracts SQL queries from the application logic.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def create_case(
        self,
        name: str,
        user_name: str,
        contact_name: str,
        source_path: str = "",
        case_uuid: Optional[str] = None
    ) -> int:
        """Create a new case record and return its ID."""
        if not case_uuid:
            case_uuid = str(uuid.uuid4())

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO cases (name, case_uuid, user_name, contact_name, source_path)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
                """,
                (name, case_uuid, user_name, contact_name, source_path)
            )
            result = cursor.fetchone()
            if result is None:
                raise ValueError("Failed to create case")
            return int(result[0])

    def get_case(self, case_id: int) -> Optional[dict[str, Any]]:
        """Retrieve case metadata."""
        with get_db_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
            return dict(row) if row else None

    def get_case_by_name(self, name: str) -> Optional[dict[str, Any]]:
        """Retrieve case by name."""
        with get_db_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM cases WHERE name = ?", (name,)).fetchone()
            return dict(row) if row else None

    def get_case_by_uuid(self, uuid: str) -> Optional[dict[str, Any]]:
        """Retrieve case by UUID."""
        with get_db_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM cases WHERE case_uuid = ?", (uuid,)).fetchone()
            return dict(row) if row else None

    def add_message(self, case_id: int, msg: MessageDict) -> int:
        """Insert a raw message into the evidence table."""
        with get_db_connection(self.db_path) as conn:
            # Parse timestamp safely
            try:
                # msg["timestamp"] is already int/float in MessageDict, but let's be safe
                ts = int(msg.get("timestamp", 0))
            except (ValueError, TypeError):
                ts = 0

            cursor = conn.execute(
                """
                INSERT INTO messages (
                    case_id, timestamp, date, time, source,
                    direction, body, media_type, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    case_id,
                    ts,
                    msg.get("date", ""),
                    msg.get("time", ""),
                    msg.get("source", "unknown"),
                    msg.get("direction", "unknown"),
                    msg.get("body", ""),
                    msg.get("type", "text"),  # Mapped 'type' -> 'media_type'
                    0,  # Duration not in MessageDict
                )
            )
            result = cursor.fetchone()
            if result is None:
                raise ValueError("Failed to insert message")
            return int(result[0])

    def add_call(self, case_id: int, call: dict[str, Any]) -> int:
        """Insert a call record."""
        with get_db_connection(self.db_path) as conn:
            try:
                ts = int(call.get("timestamp", 0))
            except (ValueError, TypeError):
                ts = 0

            cursor = conn.execute(
                """
                INSERT INTO calls (
                    case_id, timestamp, date, time, source,
                    direction, duration, call_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    case_id,
                    ts,
                    call.get("date", ""),
                    call.get("time", ""),
                    call.get("source", "unknown"),
                    call.get("direction", "unknown"),
                    call.get("duration", 0),
                    call.get("type", "phone_call"),
                )
            )
            result = cursor.fetchone()
            if result is None:
                raise ValueError("Failed to insert call")
            return int(result[0])

    def get_calls(self, case_id: int) -> list[dict[str, Any]]:
        """Retrieve all calls for a case."""
        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM calls WHERE case_id = ? ORDER BY timestamp ASC",
                (case_id,)
            ).fetchall()
            return [dict(row) for row in rows]



    def add_analysis(self, message_id: int, analysis: dict[str, Any]) -> None:
        """Insert or update analysis results for a message."""
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO message_analysis (
                    message_id, is_hurtful, severity, is_apology,
                    sentiment_score, patterns_json, keywords_json, supportive_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    1 if analysis.get("is_hurtful") else 0,
                    analysis.get("severity"),
                    1 if analysis.get("is_apology") else 0,
                    analysis.get("sentiment_score", 0.0),
                    json.dumps(analysis.get("patterns", [])),
                    json.dumps(analysis.get("keywords", [])),
                    json.dumps(analysis.get("supportive", []))
                )
            )

    def get_messages(
        self,
        case_id: int,
        limit: int = 100,
        offset: int = 0,
        date_filter: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Retrieve distinct raw messages with optional filtering."""
        query = "SELECT * FROM messages WHERE case_id = ?"
        params: list[Any] = [case_id]

        if date_filter:
            query += " AND date = ?"
            params.append(date_filter)

        query += " ORDER BY timestamp ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_message_count(self, case_id: int) -> int:
        """Get total message count for a case."""
        with get_db_connection(self.db_path) as conn:
            result = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE case_id = ?",
                (case_id,)
            ).fetchone()
            return int(result[0]) if result else 0

    def get_daily_stats(self, case_id: int) -> list[dict[str, Any]]:
        """Get daily aggregation of messages and hurtful instances."""
        query = """
            SELECT 
                m.date,
                COUNT(*) as total_messages,
                SUM(CASE WHEN m.direction = 'sent' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN m.direction = 'received' THEN 1 ELSE 0 END) as received,
                SUM(CASE WHEN ma.is_hurtful = 1 THEN 1 ELSE 0 END) as hurtful_count
            FROM messages m
            LEFT JOIN message_analysis ma ON m.id = ma.message_id
            WHERE m.case_id = ?
            GROUP BY m.date
            ORDER BY m.date
        """
        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(query, (case_id,)).fetchall()
            return [dict(row) for row in rows]

    def get_pattern_stats(self, case_id: int) -> list[dict[str, Any]]:
        """Get count of patterns detected."""
        # Since patterns are JSON, we might have to process them in python if sqlite json extension isn't reliable everywhere.
        # But efficiently: we can just select the JSON patterns and aggregate in python.
        query = """
            SELECT ma.patterns_json, m.direction
            FROM message_analysis ma
            JOIN messages m ON ma.message_id = m.id
            WHERE m.case_id = ? AND ma.patterns_json IS NOT NULL
        """
        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(query, (case_id,)).fetchall()
            return [dict(row) for row in rows]

    def search_messages(
        self,
        case_id: int,
        query_text: Optional[str] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        direction: Optional[str] = None,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Search messages with filters."""
        sql = """
            SELECT m.*, ma.is_hurtful, ma.severity, ma.patterns_json
            FROM messages m
            LEFT JOIN message_analysis ma ON m.id = ma.message_id
            WHERE m.case_id = ?
        """
        params: list[Any] = [case_id]

        if query_text:
            sql += " AND m.body LIKE ?"
            params.append(f"%{query_text}%")

        if date_start:
            sql += " AND m.date >= ?"
            params.append(date_start)

        if date_end:
            sql += " AND m.date <= ?"
            params.append(date_end)

        if direction:
            sql += " AND m.direction LIKE ?"
            params.append(f"%{direction}%")

        sql += " ORDER BY m.timestamp DESC LIMIT ?"
        params.append(limit)

        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

