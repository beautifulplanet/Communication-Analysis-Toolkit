import uuid
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import sqlite3

from engine.db import get_db_connection

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
            return cursor.fetchone()[0]

    def get_case(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve case metadata."""
        with get_db_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
            return dict(row) if row else None

    def add_message(self, case_id: int, msg: Dict[str, Any]) -> int:
        """Insert a raw message into the evidence table."""
        with get_db_connection(self.db_path) as conn:
            # Parse timestamp safely
            try:
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
                    msg.get("media_type", "text"),
                    msg.get("duration", 0)
                )
            )
            return cursor.fetchone()[0]

    def add_analysis(self, message_id: int, analysis: Dict[str, Any]) -> None:
        """Insert or update analysis results for a message."""
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO message_analysis (
                    message_id, is_hurtful, severity, is_apology, 
                    sentiment_score, patterns_json, keywords_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    1 if analysis.get("is_hurtful") else 0,
                    analysis.get("severity"),
                    1 if analysis.get("is_apology") else 0,
                    analysis.get("sentiment_score", 0.0),
                    json.dumps(analysis.get("patterns", [])),
                    json.dumps(analysis.get("keywords", []))
                )
            )

    def get_messages(
        self, 
        case_id: int, 
        limit: int = 100, 
        offset: int = 0,
        date_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve distinct raw messages with optional filtering."""
        query = "SELECT * FROM messages WHERE case_id = ?"
        params = [case_id]
        
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
            return conn.execute(
                "SELECT COUNT(*) FROM messages WHERE case_id = ?", 
                (case_id,)
            ).fetchone()[0]
