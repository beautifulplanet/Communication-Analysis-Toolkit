"""
================================================================================
Communication Analysis Toolkit — Data Ingestion Module
================================================================================

Parsers for all supported data sources:
  - SMS XML backups (SMS Backup & Restore format)
  - Call log XML backups
  - Signal calls from decrypted database
  - Generic JSON message files
  - CSV message files

Each parser returns a standardized list of message/call dicts with fields:
  source, timestamp, datetime, date, time, direction, body/duration, type

Extracted from analyzer.py for cleaner separation of concerns.
================================================================================
"""

import xml.etree.ElementTree as ET

try:
    import defusedxml.ElementTree as SafeET
except ImportError:
    SafeET = None  # Fall back to stdlib if defusedxml not installed

import json
import os
import re
import sqlite3
from datetime import datetime
from typing import Any

from engine.logger import logger
from engine.types import CallDict, MessageDict

# ==============================================================================
# HELPERS
# ==============================================================================


def phone_match(number: str, suffix: str) -> bool:
    """Check if a phone number matches the target contact by suffix."""
    if not number or not suffix:
        return False
    clean = re.sub(r"[^\d]", "", number)
    return clean.endswith(suffix)


# ==============================================================================
# SMS XML PARSER
# ==============================================================================


def parse_sms(path: str, config: dict[str, Any]) -> list[MessageDict]:
    """Parse SMS XML backup (SMS Backup & Restore format)."""
    if not path:
        return []
    logger.info("parsing_sms_started", path=path)
    messages: list[MessageDict] = []
    suffix = config.get("phone_suffix", "")
    contact_phone = config.get("contact_phone", "")

    try:
        # Use defusedxml if available (blocks XML bombs), otherwise stdlib
        parser = SafeET if SafeET else ET
        context = parser.iterparse(path, events=("end",))
    except FileNotFoundError:
        logger.warning("sms_file_not_found", path=path)
        return []
    for _, elem in context:
        if elem.tag == "sms":
            addr = elem.get("address", "")
            if phone_match(addr, suffix) or (contact_phone and contact_phone in addr):
                sms_type = int(elem.get("type", "0"))
                if sms_type in (1, 2):
                    ts = int(elem.get("date", "0"))
                    dt = datetime.fromtimestamp(ts / 1000)
                    messages.append(
                        {
                            "source": "sms",
                            "timestamp": ts,
                            "datetime": dt,
                            "date": dt.strftime("%Y-%m-%d"),
                            "time": dt.strftime("%H:%M:%S"),
                            "direction": "received" if sms_type == 1 else "sent",
                            "body": elem.get("body", ""),
                            "type": "text",
                        }
                    )
            elem.clear()
        elif elem.tag == "mms":
            elem.clear()
    logger.info("sms_parsing_complete", count=len(messages))
    return messages


# ==============================================================================
# CALL LOG XML PARSER
# ==============================================================================


def parse_calls(path: str, config: dict[str, Any]) -> list[CallDict]:
    """Parse Call log XML backup."""
    if not path or not os.path.exists(path):
        return []
    logger.info("parsing_calls_started", path=path)
    calls: list[CallDict] = []
    suffix = config.get("phone_suffix", "")
    contact_phone = config.get("contact_phone", "")

    _parse = SafeET.iterparse if SafeET else ET.iterparse
    context = _parse(path, events=("end",))
    for _, elem in context:
        if elem.tag == "call":
            number = elem.get("number", "")
            if phone_match(number, suffix) or (contact_phone and contact_phone in number):
                call_type = int(elem.get("type", "0"))
                ts = int(elem.get("date", "0"))
                dur = int(elem.get("duration", "0"))
                dt = datetime.fromtimestamp(ts / 1000)
                type_map = {1: "incoming", 2: "outgoing", 3: "missed", 5: "rejected"}
                calls.append(
                    {
                        "source": "phone",
                        "timestamp": ts,
                        "datetime": dt,
                        "date": dt.strftime("%Y-%m-%d"),
                        "time": dt.strftime("%H:%M:%S"),
                        "direction": type_map.get(call_type, "unknown"),
                        "duration": dur,
                        "type": "phone_call",
                    }
                )
            elem.clear()
            elem.clear()
    logger.info("call_parsing_complete", count=len(calls))
    return calls


# ==============================================================================
# SIGNAL CALLS PARSER (SQLite)
# ==============================================================================


def parse_signal_calls(db_path: str, config: dict[str, Any]) -> list[CallDict]:
    """Parse Signal calls from decrypted database."""
    if not db_path or not os.path.exists(db_path):
        return []
    logger.info("parsing_signal_calls_started", path=db_path)
    calls: list[CallDict] = []
    contact_phone = config.get("contact_phone", "")
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT _id FROM recipient WHERE e164 = ?", (contact_phone,))
        row = c.fetchone()
        if not row:
            logger.warning("signal_contact_not_found", contact_phone=contact_phone)
            conn.close()
            return calls
        recipient_id = row[0]

        c.execute("PRAGMA table_info(call)")
        call_cols = [col[1] for col in c.fetchall()]
        c.execute("SELECT * FROM call WHERE peer = ?", (recipient_id,))
        for row in c.fetchall():
            row_dict = dict(zip(call_cols, row))
            ts = row_dict.get("timestamp", 0)
            dt = datetime.fromtimestamp(ts / 1000)
            direction = "incoming" if row_dict.get("direction", 0) == 0 else "outgoing"
            "video_call" if row_dict.get("type", 0) == 1 else "audio_call"
            row_dict.get("event", 0)
            calls.append(
                {
                    "source": "signal",
                    "timestamp": ts,
                    "datetime": dt,
                    "date": dt.strftime("%Y-%m-%d"),
                    "time": dt.strftime("%H:%M:%S"),
                    "direction": direction,
                    "duration": 0,
                    "type": "signal_call",
                }
            )
        conn.close()
        conn.close()
    except Exception as e:
        logger.error("signal_parsing_error", error=str(e))
    logger.info("signal_calls_parsed", count=len(calls))
    return calls


# ==============================================================================
# JSON MESSAGE PARSER
# ==============================================================================


def parse_json_messages(json_path: str, source_label: str = "json") -> list[MessageDict]:
    """Load messages from a JSON file (generic format)."""
    if not json_path or not os.path.exists(json_path):
        return []
    # Guard against extremely large files (500MB limit)
    file_size = os.path.getsize(json_path)
    if file_size > 500 * 1024 * 1024:
        logger.warning("json_file_too_large", path=json_path, size_mb=file_size / 1024 / 1024)
        return []
    logger.info("loading_json_messages", path=json_path)
    messages: list[MessageDict] = []
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        for msg in data.get("messages", []):
            body = msg.get("body", "")
            direction = msg.get("direction", "unknown")
            ts_str = msg.get("datetime", msg.get("timestamp", ""))
            ts_ms = msg.get("timestamp_ms", msg.get("timestamp", 0))

            if isinstance(ts_str, str) and ts_str and ts_str != "unknown":
                try:
                    dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
            elif isinstance(ts_ms, (int, float)) and ts_ms > 0:
                dt = datetime.fromtimestamp(ts_ms / 1000)
            else:
                continue

            messages.append(
                {
                    "source": source_label,
                    "timestamp": int(ts_ms)
                    if isinstance(ts_ms, (int, float))
                    else int(dt.timestamp() * 1000),
                    "datetime": dt,
                    "date": dt.strftime("%Y-%m-%d"),
                    "time": dt.strftime("%H:%M:%S"),
                    "direction": direction,
                    "body": body,
                    "type": "text" if body else "media",
                }
            )
    except Exception as e:
        logger.error("json_parsing_error", error=str(e))
    sent = sum(1 for m in messages if m["direction"] == "sent")
    recv = sum(1 for m in messages if m["direction"] == "received")
    logger.info("json_messages_parsed", count=len(messages), sent=sent, received=recv)
    return messages


# ==============================================================================
# CSV MESSAGE PARSER
# ==============================================================================


def parse_csv_messages(csv_path: str) -> list[MessageDict]:
    """Load messages from CSV (columns: datetime, direction, body)."""
    if not csv_path or not os.path.exists(csv_path):
        return []
    import csv as csv_mod

    logger.info("loading_csv_messages", path=csv_path)
    messages: list[MessageDict] = []
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv_mod.DictReader(f)
            for row in reader:
                dt_str = row.get("datetime", row.get("date", ""))
                direction = row.get("direction", row.get("type", "unknown"))
                body = row.get("body", row.get("message", row.get("text", "")))
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        dt = datetime.strptime(dt_str, "%Y-%m-%d")
                    except ValueError:
                        continue
                messages.append(
                    {
                        "source": "csv",
                        "timestamp": int(dt.timestamp() * 1000),
                        "datetime": dt,
                        "date": dt.strftime("%Y-%m-%d"),
                        "time": dt.strftime("%H:%M:%S"),
                        "direction": direction,
                        "body": body,
                        "type": "text",
                    }
                )
    except Exception as e:
        logger.error("csv_parsing_error", error=str(e))
    logger.info("csv_messages_parsed", count=len(messages))
    return messages
