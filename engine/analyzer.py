"""
================================================================================
Communication Analysis Toolkit — Analysis Engine
================================================================================

Generic, reusable communication analysis engine. Accepts data from any source
(SMS XML backups, Signal databases, CSV imports, JSON) and produces detailed
reports on behavioral patterns, communication dynamics, and interaction health.

USAGE:
  1. Place source data in a case folder (e.g., cases/my_case/source_data/)
  2. Create a config.json with case parameters
  3. Run: python -m engine.analyzer --config cases/my_case/config.json

OUTPUT:
  - TIMELINE.md       — Day-by-day narrative timeline
  - ANALYSIS.md       — Comprehensive statistics & pattern summary
  - EVIDENCE.md       — Verified pattern instances with full quotes
  - DATA.json         — Machine-readable full dataset
  - AI_PROMPTS.md     — Prompts for external AI auditing

================================================================================
"""

import xml.etree.ElementTree as ET
try:
    import defusedxml.ElementTree as SafeET
except ImportError:
    SafeET = None  # Fall back to stdlib if defusedxml not installed
import sqlite3
import json
import os
import re
import sys
import argparse
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional

from engine.patterns import (
    is_directed_hurtful,
    detect_patterns,
    PATTERN_LABELS,
    PATTERN_DESCRIPTIONS,
    PATTERN_SEVERITY,
)
from engine.patterns_supportive import (
    detect_supportive_patterns,
    SUPPORTIVE_LABELS,
    SUPPORTIVE_DESCRIPTIONS,
    SUPPORTIVE_VALUE,
)
from engine.relationship_health import (
    calculate_gottman_ratio,
    calculate_health_score,
)


# ==============================================================================
# SECURITY HELPERS
# ==============================================================================

_MD_ESCAPE_RE = re.compile(r'([\\`*_\{\}\[\]()#+\-.!|>~])')

def escape_md(text: str) -> str:
    """Escape markdown special characters in user-supplied text.

    Prevents markdown injection where message bodies could break report
    formatting or inject headings/links/images.
    """
    if not text:
        return text
    return _MD_ESCAPE_RE.sub(r'\\\1', text)


# ==============================================================================
# CONFIGURATION
# ==============================================================================

DEFAULT_CONFIG = {
    "case_name": "Untitled Case",
    "user_label": "User A",
    "contact_label": "User B",
    "contact_phone": "",
    "phone_suffix": "",

    "sms_xml": "",
    "calls_xml": "",
    "signal_db": "",
    "signal_sent_json": "",
    "manual_signal_json": "",
    "signal_desktop_json": "",

    "output_dir": "./output",
    "date_start": "",
    "date_end": "",
}


def load_config(config_path: str) -> dict:
    """Load case configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        raw = f.read()
        if len(raw) > 10 * 1024 * 1024:  # 10 MB sanity limit
            raise ValueError("Config file too large")
        user_config = json.loads(raw)
    config = {**DEFAULT_CONFIG, **user_config}

    # Default date range: 1 year ago to today
    if not config["date_start"]:
        config["date_start"] = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if not config["date_end"]:
        config["date_end"] = datetime.now().strftime('%Y-%m-%d')

    # Path traversal protection: validate output_dir is under the config directory
    config_dir = os.path.realpath(os.path.dirname(config_path))
    output_resolved = os.path.realpath(os.path.join(config_dir, config["output_dir"]))
    if not output_resolved.startswith(config_dir):
        raise ValueError(f"output_dir escapes case directory: {config['output_dir']}")
    config["output_dir"] = output_resolved
    os.makedirs(config["output_dir"], exist_ok=True)
    return config


# ==============================================================================
# DATA INGESTION
# ==============================================================================

def phone_match(number: str, suffix: str) -> bool:
    """Check if a phone number matches the target contact by suffix."""
    if not number or not suffix:
        return False
    clean = re.sub(r'[^\d]', '', number)
    return clean.endswith(suffix)


def parse_sms(path: str, config: dict) -> List[dict]:
    """Parse SMS XML backup (SMS Backup & Restore format)."""
    if not path:
        return []
    print(f"  Parsing SMS from {path}...")
    messages = []
    suffix = config.get("phone_suffix", "")
    contact_phone = config.get("contact_phone", "")

    try:
        # Use defusedxml if available (blocks XML bombs), otherwise stdlib
        parser = SafeET if SafeET else ET
        context = parser.iterparse(path, events=('end',))
    except FileNotFoundError:
        print(f"    Warning: SMS file not found: {path}")
        return []
    for event, elem in context:
        if elem.tag == 'sms':
            addr = elem.get('address', '')
            if phone_match(addr, suffix) or (contact_phone and contact_phone in addr):
                sms_type = int(elem.get('type', '0'))
                if sms_type in (1, 2):
                    ts = int(elem.get('date', '0'))
                    dt = datetime.fromtimestamp(ts / 1000)
                    messages.append({
                        'source': 'sms',
                        'timestamp': ts,
                        'datetime': dt,
                        'date': dt.strftime('%Y-%m-%d'),
                        'time': dt.strftime('%H:%M:%S'),
                        'direction': 'received' if sms_type == 1 else 'sent',
                        'body': elem.get('body', ''),
                        'type': 'text',
                    })
            elem.clear()
        elif elem.tag == 'mms':
            elem.clear()
    print(f"    Found {len(messages)} SMS messages")
    return messages


def parse_calls(path: str, config: dict) -> List[dict]:
    """Parse Call log XML backup."""
    if not path or not os.path.exists(path):
        return []
    print(f"  Parsing calls from {path}...")
    calls = []
    suffix = config.get("phone_suffix", "")
    contact_phone = config.get("contact_phone", "")

    _parse = SafeET.iterparse if SafeET else ET.iterparse
    context = _parse(path, events=('end',))
    for event, elem in context:
        if elem.tag == 'call':
            number = elem.get('number', '')
            if phone_match(number, suffix) or (contact_phone and contact_phone in number):
                call_type = int(elem.get('type', '0'))
                ts = int(elem.get('date', '0'))
                dur = int(elem.get('duration', '0'))
                dt = datetime.fromtimestamp(ts / 1000)
                type_map = {1: 'incoming', 2: 'outgoing', 3: 'missed', 5: 'rejected'}
                calls.append({
                    'source': 'phone',
                    'timestamp': ts,
                    'datetime': dt,
                    'date': dt.strftime('%Y-%m-%d'),
                    'time': dt.strftime('%H:%M:%S'),
                    'direction': type_map.get(call_type, 'unknown'),
                    'duration_seconds': dur,
                    'type': 'phone_call',
                })
            elem.clear()
    print(f"    Found {len(calls)} phone calls")
    return calls


def parse_signal_calls(db_path: str, config: dict) -> List[dict]:
    """Parse Signal calls from decrypted database."""
    if not db_path or not os.path.exists(db_path):
        return []
    print(f"  Parsing Signal calls from {db_path}...")
    calls = []
    contact_phone = config.get("contact_phone", "")
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT _id FROM recipient WHERE e164 = ?", (contact_phone,))
        row = c.fetchone()
        if not row:
            print("    Contact not found in Signal DB")
            conn.close()
            return calls
        recipient_id = row[0]

        c.execute("PRAGMA table_info(call)")
        call_cols = [col[1] for col in c.fetchall()]
        c.execute("SELECT * FROM call WHERE peer = ?", (recipient_id,))
        for row in c.fetchall():
            row_dict = dict(zip(call_cols, row))
            ts = row_dict.get('timestamp', 0)
            dt = datetime.fromtimestamp(ts / 1000)
            direction = 'incoming' if row_dict.get('direction', 0) == 0 else 'outgoing'
            call_type = 'video_call' if row_dict.get('type', 0) == 1 else 'audio_call'
            event = row_dict.get('event', 0)
            event_map = {0: 'ongoing', 1: 'accepted', 2: 'not_accepted', 3: 'missed',
                         4: 'deleted', 5: 'group', 6: 'joined', 7: 'declined', 8: 'ring'}
            calls.append({
                'source': 'signal',
                'timestamp': ts,
                'datetime': dt,
                'date': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M:%S'),
                'direction': direction,
                'call_type': call_type,
                'event': event_map.get(event, str(event)),
                'type': 'signal_call',
            })
        conn.close()
    except Exception as e:
        print(f"    Error: {e}")
    print(f"    Found {len(calls)} Signal calls")
    return calls


def parse_json_messages(json_path: str, source_label: str = 'json') -> List[dict]:
    """Load messages from a JSON file (generic format)."""
    if not json_path or not os.path.exists(json_path):
        return []
    # Guard against extremely large files (500MB limit)
    file_size = os.path.getsize(json_path)
    if file_size > 500 * 1024 * 1024:
        print(f"    WARNING: {json_path} is {file_size / 1024 / 1024:.0f}MB — skipping (500MB limit)")
        return []
    print(f"  Loading messages from {json_path}...")
    messages = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for msg in data.get('messages', []):
            body = msg.get('body', '')
            direction = msg.get('direction', 'unknown')
            ts_str = msg.get('datetime', msg.get('timestamp', ''))
            ts_ms = msg.get('timestamp_ms', msg.get('timestamp', 0))

            if isinstance(ts_str, str) and ts_str and ts_str != 'unknown':
                try:
                    dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
            elif isinstance(ts_ms, (int, float)) and ts_ms > 0:
                dt = datetime.fromtimestamp(ts_ms / 1000)
            else:
                continue

            messages.append({
                'source': source_label,
                'timestamp': ts_ms if isinstance(ts_ms, (int, float)) else int(dt.timestamp() * 1000),
                'datetime': dt,
                'date': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M:%S'),
                'direction': direction,
                'body': body,
                'type': 'text' if body else 'media',
            })
    except Exception as e:
        print(f"    Error: {e}")
    sent = sum(1 for m in messages if m['direction'] == 'sent')
    recv = sum(1 for m in messages if m['direction'] == 'received')
    print(f"    Found {len(messages)} messages ({sent} sent, {recv} received)")
    return messages


def parse_csv_messages(csv_path: str) -> List[dict]:
    """Load messages from CSV (columns: datetime, direction, body)."""
    if not csv_path or not os.path.exists(csv_path):
        return []
    import csv as csv_mod
    print(f"  Loading messages from CSV {csv_path}...")
    messages = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv_mod.DictReader(f)
            for row in reader:
                dt_str = row.get('datetime', row.get('date', ''))
                direction = row.get('direction', row.get('type', 'unknown'))
                body = row.get('body', row.get('message', row.get('text', '')))
                try:
                    dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        dt = datetime.strptime(dt_str, '%Y-%m-%d')
                    except ValueError:
                        continue
                messages.append({
                    'source': 'csv',
                    'timestamp': int(dt.timestamp() * 1000),
                    'datetime': dt,
                    'date': dt.strftime('%Y-%m-%d'),
                    'time': dt.strftime('%H:%M:%S'),
                    'direction': direction,
                    'body': body,
                    'type': 'text',
                })
    except Exception as e:
        print(f"    Error: {e}")
    print(f"    Found {len(messages)} messages from CSV")
    return messages


# ==============================================================================
# ANALYSIS ENGINE
# ==============================================================================

def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"


def analyze_all(config: dict, all_texts: List[dict], all_calls: List[dict]) -> tuple:
    """Run all analysis on the combined data."""
    start = datetime.strptime(config["date_start"], '%Y-%m-%d')
    end = datetime.strptime(config["date_end"], '%Y-%m-%d')

    # Build daily data structure
    days = {}
    current = start
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        days[date_str] = {
            'date': date_str,
            'weekday': current.strftime('%A'),
            'had_contact': False,
            'messages': {'sent': 0, 'received': 0, 'all': []},
            'calls': {'incoming': 0, 'outgoing': 0, 'missed': 0, 'total_seconds': 0},
            'hurtful': {'from_user': [], 'from_contact': []},
            'patterns': {'from_user': [], 'from_contact': []},
            'supportive': {'from_user': [], 'from_contact': []},
        }
        current += timedelta(days=1)

    # Populate messages
    for msg in all_texts:
        d = msg['date']
        if d not in days:
            continue
        days[d]['had_contact'] = True
        if msg['direction'] == 'sent':
            days[d]['messages']['sent'] += 1
        else:
            days[d]['messages']['received'] += 1
        days[d]['messages']['all'].append(msg)

        # Hurtful language check
        is_h, words, sev = is_directed_hurtful(msg.get('body', ''), msg['direction'])
        if is_h:
            entry = {
                'time': msg['time'],
                'words': words,
                'severity': sev,
                'preview': (msg.get('body', '')[:150] + '...') if len(msg.get('body', '')) > 150 else msg.get('body', ''),
                'source': msg.get('source', 'unknown'),
            }
            if msg['direction'] == 'sent':
                days[d]['hurtful']['from_user'].append(entry)
            else:
                days[d]['hurtful']['from_contact'].append(entry)

        # Pattern detection
        pattern_results = detect_patterns(msg.get('body', ''), msg['direction'])
        if pattern_results:
            for pattern_type, matched, full_msg in pattern_results:
                entry = {
                    'time': msg['time'],
                    'pattern': pattern_type,
                    'matched': matched,
                    'message': (full_msg[:200] + '...') if len(full_msg) > 200 else full_msg,
                    'source': msg.get('source', 'unknown'),
                }
                if msg['direction'] == 'sent':
                    days[d]['patterns']['from_user'].append(entry)
                else:
                    days[d]['patterns']['from_contact'].append(entry)

        # Supportive pattern detection
        supportive_results = detect_supportive_patterns(msg.get('body', ''), msg['direction'])
        if supportive_results:
            for pattern_type, matched, full_msg in supportive_results:
                entry = {
                    'time': msg['time'],
                    'pattern': pattern_type,
                    'matched': matched,
                    'message': (full_msg[:200] + '...') if len(full_msg) > 200 else full_msg,
                    'source': msg.get('source', 'unknown'),
                }
                if msg['direction'] == 'sent':
                    days[d]['supportive']['from_user'].append(entry)
                else:
                    days[d]['supportive']['from_contact'].append(entry)

    # Populate calls
    for call in all_calls:
        d = call['date']
        if d not in days:
            continue
        days[d]['had_contact'] = True
        direction = call.get('direction', '')
        if direction in ('incoming', 'accepted'):
            days[d]['calls']['incoming'] += 1
        elif direction == 'outgoing':
            days[d]['calls']['outgoing'] += 1
        elif direction in ('missed', 'not_accepted', 'declined', 'rejected'):
            days[d]['calls']['missed'] += 1
        days[d]['calls']['total_seconds'] += call.get('duration_seconds', 0)

    # Identify communication gaps
    sorted_dates = sorted(days.keys())
    contact_dates = [d for d in sorted_dates if days[d]['had_contact']]

    gaps = []
    for i in range(len(contact_dates) - 1):
        d1 = datetime.strptime(contact_dates[i], '%Y-%m-%d')
        d2 = datetime.strptime(contact_dates[i + 1], '%Y-%m-%d')
        gap_days = (d2 - d1).days - 1
        if gap_days >= 3:
            prev_day = days[contact_dates[i]]
            was_heated = (len(prev_day['hurtful']['from_user']) + len(prev_day['hurtful']['from_contact']) > 0)
            reason = 'After conflict' if was_heated else 'Unknown'
            gaps.append({
                'start': (d1 + timedelta(days=1)).strftime('%Y-%m-%d'),
                'end': (d2 - timedelta(days=1)).strftime('%Y-%m-%d'),
                'days': gap_days,
                'reason': reason,
            })
    gaps.sort(key=lambda g: g['days'], reverse=True)

    return days, gaps


# ==============================================================================
# REPORT GENERATION
# ==============================================================================

def generate_analysis_report(config: dict, days: dict, gaps: list) -> str:
    """Generate ANALYSIS.md — comprehensive statistics."""
    user = escape_md(config["user_label"])
    contact = escape_md(config["contact_label"])
    case_name = escape_md(config["case_name"])
    sorted_dates = sorted(days.keys())
    contact_days = [d for d in sorted_dates if days[d]['had_contact']]
    no_contact = [d for d in sorted_dates if not days[d]['had_contact']]

    total_sent = sum(days[d]['messages']['sent'] for d in sorted_dates)
    total_received = sum(days[d]['messages']['received'] for d in sorted_dates)
    total_calls = sum(days[d]['calls']['incoming'] + days[d]['calls']['outgoing'] + days[d]['calls']['missed'] for d in sorted_dates)
    total_talk = sum(days[d]['calls']['total_seconds'] for d in sorted_dates)

    total_hurtful_user = sum(len(days[d]['hurtful']['from_user']) for d in sorted_dates)
    total_hurtful_contact = sum(len(days[d]['hurtful']['from_contact']) for d in sorted_dates)

    # Severity breakdowns
    h_user_severe = sum(1 for d in sorted_dates for h in days[d]['hurtful']['from_user'] if h['severity'] == 'severe')
    h_contact_severe = sum(1 for d in sorted_dates for h in days[d]['hurtful']['from_contact'] if h['severity'] == 'severe')
    h_user_moderate = sum(1 for d in sorted_dates for h in days[d]['hurtful']['from_user'] if h['severity'] == 'moderate')
    h_contact_moderate = sum(1 for d in sorted_dates for h in days[d]['hurtful']['from_contact'] if h['severity'] == 'moderate')
    h_user_mild = sum(1 for d in sorted_dates for h in days[d]['hurtful']['from_user'] if h['severity'] == 'mild')
    h_contact_mild = sum(1 for d in sorted_dates for h in days[d]['hurtful']['from_contact'] if h['severity'] == 'mild')

    # Pattern counts
    patterns_user = defaultdict(int)
    patterns_contact = defaultdict(int)
    for d in sorted_dates:
        for entry in days[d]['patterns']['from_user']:
            patterns_user[entry['pattern']] += 1
        for entry in days[d]['patterns']['from_contact']:
            patterns_contact[entry['pattern']] += 1

    lines = []
    lines.append(f"# Communication Analysis\n")
    lines.append(f"**Case**: {case_name}")
    lines.append(f"**Parties**: {user} (analyzed user) vs. {contact}")
    lines.append(f"**Analysis Period**: {config['date_start']} to {config['date_end']} ({len(sorted_dates)} days)")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")

    lines.append("## Executive Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Days Analyzed | {len(sorted_dates)} |")
    lines.append(f"| Days WITH Contact | {len(contact_days)} ({100 * len(contact_days) // max(len(sorted_dates), 1)}%) |")
    lines.append(f"| Days WITHOUT Contact | {len(no_contact)} ({100 * len(no_contact) // max(len(sorted_dates), 1)}%) |")
    lines.append(f"| Messages Sent ({user}) | {total_sent:,} |")
    lines.append(f"| Messages Received ({contact}) | {total_received:,} |")
    lines.append(f"| Total Calls | {total_calls:,} |")
    lines.append(f"| Total Talk Time | {format_duration(total_talk)} |")
    lines.append("")

    lines.append("## Hurtful Language Summary (Context-Aware)\n")
    lines.append("*Only flags language directed at the other person. Benign uses excluded.*\n")
    lines.append(f"| Severity | {user} | {contact} |")
    lines.append("|----------|--------|---------|")
    lines.append(f"| 🔴 Severe | {h_user_severe} | {h_contact_severe} |")
    lines.append(f"| 🟠 Moderate | {h_user_moderate} | {h_contact_moderate} |")
    lines.append(f"| 🟡 Mild | {h_user_mild} | {h_contact_mild} |")
    lines.append(f"| **Total** | **{total_hurtful_user}** | **{total_hurtful_contact}** |")
    lines.append("")

    lines.append("## Behavioral Pattern Summary\n")
    lines.append("*Patterns detected using clinical taxonomy (DARVO, Gottman, Coercive Control, etc.)*\n")
    all_patterns = sorted(set(list(patterns_user.keys()) + list(patterns_contact.keys())),
                          key=lambda p: PATTERN_SEVERITY.get(p, 0), reverse=True)
    if all_patterns:
        lines.append(f"| Pattern | {user} | {contact} | Source |")
        lines.append("|---------|--------|---------|--------|")
        for p in all_patterns:
            label = PATTERN_LABELS.get(p, p)
            desc = PATTERN_DESCRIPTIONS.get(p, '')
            source = desc.split('(')[-1].rstrip(')') if '(' in desc else ''
            lines.append(f"| {label} | {patterns_user.get(p, 0)} | {patterns_contact.get(p, 0)} | {source} |")
        lines.append(f"| **Total** | **{sum(patterns_user.values())}** | **{sum(patterns_contact.values())}** | |")
    lines.append("")

    # Communication gaps
    lines.append("## Communication Gaps (3+ days)\n")
    lines.append("| Start | End | Days Silent | Reason |")
    lines.append("|-------|-----|-------------|--------|")
    for gap in gaps[:25]:
        lines.append(f"| {gap['start']} | {gap['end']} | **{gap['days']}** | {gap['reason']} |")
    lines.append("")

    return '\n'.join(lines)


def generate_evidence_report(config: dict, days: dict) -> str:
    """Generate EVIDENCE.md — verified manipulation instances with full quotes."""
    user = escape_md(config["user_label"])
    contact = escape_md(config["contact_label"])
    sorted_dates = sorted(days.keys())

    lines = []
    lines.append(f"# Verified Behavioral Pattern Evidence\n")
    lines.append(f"**Case**: {escape_md(config['case_name'])}")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("**Method**: Context-aware clinical pattern matching\n")
    lines.append("---\n")

    # Hurtful from contact
    lines.append(f"## Hurtful Language FROM {contact}\n")
    all_hurtful_contact = []
    for d in sorted_dates:
        for h in days[d]['hurtful']['from_contact']:
            all_hurtful_contact.append({**h, 'date': d})

    for severity, emoji, desc in [
        ('severe', '🔴', 'Personal attacks, weaponizing trauma, threats'),
        ('moderate', '🟠', 'Directed insults and profanity'),
        ('mild', '🟡', 'Dismissive language, contextual profanity'),
    ]:
        items = [h for h in all_hurtful_contact if h['severity'] == severity]
        if items:
            lines.append(f"### {emoji} {severity.title()} ({len(items)} instances) — {desc}\n")
            for h in items:
                lines.append(f"**{h['date']} {h['time']}** ({h['source'].upper()}) — Flagged: `{', '.join(h['words'])}`")
                lines.append(f"> {escape_md(h['preview'])}\n")

    # Hurtful from user
    lines.append(f"## Hurtful Language FROM {user}\n")
    all_hurtful_user = []
    for d in sorted_dates:
        for h in days[d]['hurtful']['from_user']:
            all_hurtful_user.append({**h, 'date': d})

    for severity, emoji, desc in [
        ('severe', '🔴', 'Personal attacks, weaponizing trauma, threats'),
        ('moderate', '🟠', 'Directed insults and profanity'),
        ('mild', '🟡', 'Dismissive language, contextual profanity'),
    ]:
        items = [h for h in all_hurtful_user if h['severity'] == severity]
        if items:
            lines.append(f"### {emoji} {severity.title()} ({len(items)} instances) — {desc}\n")
            for h in items:
                lines.append(f"**{h['date']} {h['time']}** ({h['source'].upper()}) — Flagged: `{', '.join(h['words'])}`")
                lines.append(f"> {escape_md(h['preview'])}\n")

    if not all_hurtful_user:
        lines.append(f"*No directed hurtful language detected from {user}.*\n")

    # Patterns from contact
    lines.append("---\n")
    lines.append(f"## Behavioral Patterns FROM {contact}\n")

    all_patterns_contact = []
    for d in sorted_dates:
        for entry in days[d]['patterns']['from_contact']:
            all_patterns_contact.append({**entry, 'date': d})

    pattern_order = sorted(set(e['pattern'] for e in all_patterns_contact),
                           key=lambda p: PATTERN_SEVERITY.get(p, 0), reverse=True)

    for pattern in pattern_order:
        items = [e for e in all_patterns_contact if e['pattern'] == pattern]
        if items:
            label = PATTERN_LABELS.get(pattern, pattern)
            lines.append(f"### {label} ({len(items)} instances)\n")
            seen = {}
            for e in items:
                key = e['message'].strip()[:100]
                if key in seen:
                    seen[key]['count'] += 1
                else:
                    seen[key] = {'entry': e, 'count': 1}
            for key, info in seen.items():
                e = info['entry']
                count_note = f" x{info['count']}" if info['count'] > 1 else ""
                lines.append(f"**{e['date']} {e['time']}{count_note}** — Matched: `{e['matched']}`")
                lines.append(f"> {escape_md(e['message'])}\n")

    # Patterns from user
    lines.append(f"## Behavioral Patterns FROM {user}\n")
    lines.append(f"> Note: Some patterns from {user} may be reactive/defensive rather than manipulative.")
    lines.append(f"> Context matters — a \"leave me alone\" request during an argument differs from a controlling ultimatum.\n")

    all_patterns_user = []
    for d in sorted_dates:
        for entry in days[d]['patterns']['from_user']:
            all_patterns_user.append({**entry, 'date': d})

    if all_patterns_user:
        pattern_order_user = sorted(set(e['pattern'] for e in all_patterns_user),
                                    key=lambda p: PATTERN_SEVERITY.get(p, 0), reverse=True)
        for pattern in pattern_order_user:
            items = [e for e in all_patterns_user if e['pattern'] == pattern]
            if items:
                label = PATTERN_LABELS.get(pattern, pattern)
                lines.append(f"### {label} ({len(items)} instances)\n")
                for e in items:
                    lines.append(f"**{e['date']} {e['time']}** — Matched: `{e['matched']}`")
                    lines.append(f"> {escape_md(e['message'])}\n")
    else:
        lines.append(f"*No manipulation patterns detected from {user}.*\n")

    return '\n'.join(lines)


def generate_timeline(config: dict, days: dict, gaps: list) -> str:
    """Generate TIMELINE.md — narrative day-by-day timeline."""
    user = escape_md(config["user_label"])
    contact = escape_md(config["contact_label"])
    sorted_dates = sorted(days.keys())

    gap_lookup = {}
    for gap in gaps:
        gap_lookup[gap['start']] = gap

    lines = []
    lines.append(f"# Communication Timeline\n")
    lines.append(f"**Case**: {escape_md(config['case_name'])}")
    lines.append(f"**Period**: {config['date_start']} to {config['date_end']}")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")

    current_month = None
    gap_shown = set()

    for d in sorted_dates:
        day = days[d]
        month = d[:7]

        if month != current_month:
            current_month = month
            dt = datetime.strptime(d, '%Y-%m-%d')
            lines.append(f"\n## {dt.strftime('%B %Y')}\n")

        if d in gap_lookup and d not in gap_shown:
            gap = gap_lookup[d]
            gap_shown.add(d)
            lines.append(f"### 📵 NO CONTACT: {gap['start']} → {gap['end']} ({gap['days']} days) — {gap['reason']}\n")
            continue

        if not day['had_contact']:
            continue

        total_msgs = day['messages']['sent'] + day['messages']['received']
        total_calls = day['calls']['incoming'] + day['calls']['outgoing'] + day['calls']['missed']
        talk = format_duration(day['calls']['total_seconds']) if day['calls']['total_seconds'] > 0 else ''

        hurtful_count = len(day['hurtful']['from_user']) + len(day['hurtful']['from_contact'])
        pattern_count = len(day['patterns']['from_user']) + len(day['patterns']['from_contact'])

        if hurtful_count >= 3 or any(h['severity'] == 'severe' for h in day['hurtful']['from_contact'] + day['hurtful']['from_user']):
            mood = "🔴 HEATED"
        elif hurtful_count >= 1 or pattern_count >= 2:
            mood = "🟠 Tense"
        elif total_msgs > 50 or total_calls > 5:
            mood = "🟢 Active"
        else:
            mood = "⚪"

        parts = []
        if total_msgs > 0:
            parts.append(f"{day['messages']['sent']}↑ {day['messages']['received']}↓ msgs")
        if total_calls > 0:
            parts.append(f"{total_calls} calls")
        if talk:
            parts.append(f"({talk})")
        summary = ' · '.join(parts) if parts else 'Contact'

        lines.append(f"### {d} ({day['weekday']}) {mood}")
        lines.append(f"_{summary}_\n")

        for h in day['hurtful']['from_contact']:
            sev_emoji = {'severe': '🔴', 'moderate': '🟠', 'mild': '🟡'}[h['severity']]
            lines.append(f"- {sev_emoji} **{contact}** [{h['severity']}]: {', '.join(h['words'])} — *\"{escape_md(h['preview'])}\"*")

        for h in day['hurtful']['from_user']:
            sev_emoji = {'severe': '🔴', 'moderate': '🟠', 'mild': '🟡'}[h['severity']]
            lines.append(f"- {sev_emoji} **{user}** [{h['severity']}]: {', '.join(h['words'])} — *\"{escape_md(h['preview'])}\"*")

        for e in day['patterns']['from_contact']:
            label = PATTERN_LABELS.get(e['pattern'], e['pattern'])
            lines.append(f"- ⚠️ **{contact}** [{label}]: *\"{escape_md(e['message'])}\"*")

        if day['hurtful']['from_contact'] or day['hurtful']['from_user'] or day['patterns']['from_contact']:
            lines.append("")

    return '\n'.join(lines)


def generate_ai_prompts(config: dict) -> str:
    """Generate AI_PROMPTS.md — prompts for external AI auditing."""
    user = escape_md(config["user_label"])
    contact = escape_md(config["contact_label"])
    return f"""# AI Audit Prompts

Use these prompts with any AI (ChatGPT, Claude, Gemini) along with the data files.
Replace placeholder names with actual identifiers as needed.

---

## 1. Objective Relationship Therapist

```
You are a licensed couples therapist with 20 years of experience.
Analyze this relationship communication data objectively:

1. Communication Health Assessment (1-10)
2. Key Patterns (positive and concerning, for BOTH parties)
3. Conflict Style Analysis (Gottman's Four Horsemen assessment)
4. Specific red flags with evidence
5. Recommendations for both parties

Base analysis ONLY on the data. Acknowledge limitations. Be balanced.

[Paste ANALYSIS.md content]
[Paste EVIDENCE.md content]
```

---

## 2. Legal/Documentation Review

```
You are a family law paralegal reviewing communication records.
Assess:

1. Are there patterns of controlling behavior from either party?
2. Is there evidence of emotional abuse patterns (DARVO, coercive control)?
3. What is the strongest evidence and what would a court find credible?
4. What are the weaknesses in this documentation?
5. What additional evidence should be gathered?

Note any false positives or weak evidence that should be excluded.

[Paste EVIDENCE.md content]
```

---

## 3. Data Integrity Auditor

```
You are a forensic data analyst. Review this communication analysis for:

1. Data completeness — what's missing?
2. Methodology soundness — are the detection methods reliable?
3. False positive assessment — which flagged items are likely benign?
4. Statistical validity — do the numbers add up?
5. Bias check — does the analysis favor either party unfairly?

[Paste ANALYSIS.md content]
```

---

## 4. Pattern-Specific Deep Dive

```
You are a clinical psychologist specializing in abusive relationship dynamics.
Focus specifically on these pattern categories detected in the data:

1. DARVO instances — are they genuine manipulation or normal conversation?
2. Gaslighting — distinguish actual reality distortion from disagreement
3. Coercive control — assess severity and pattern consistency
4. Love bombing / future faking — assess manipulation vs genuine affection

For each flagged instance, rate confidence (High/Medium/Low) that it represents
genuine manipulation vs. normal conflict communication.

[Paste EVIDENCE.md content]
```
"""


def save_data_json(config: dict, days: dict, gaps: list) -> None:
    """Save machine-readable DATA.json."""
    json_days = {}
    for d, day in days.items():
        json_days[d] = {
            'date': day['date'],
            'weekday': day['weekday'],
            'had_contact': day['had_contact'],
            'messages_sent': day['messages']['sent'],
            'messages_received': day['messages']['received'],
            'calls_in': day['calls']['incoming'],
            'calls_out': day['calls']['outgoing'],
            'calls_missed': day['calls']['missed'],
            'talk_seconds': day['calls']['total_seconds'],
            'hurtful_from_user': day['hurtful']['from_user'],
            'hurtful_from_contact': day['hurtful']['from_contact'],
            'patterns_from_user': day['patterns']['from_user'],
            'patterns_from_contact': day['patterns']['from_contact'],
        }

    data_output = {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'case': config['case_name'],
        'user': config['user_label'],
        'contact': config['contact_label'],
        'period': {'start': config['date_start'], 'end': config['date_end']},
        'days': json_days,
        'gaps': gaps,
    }

    output_path = os.path.join(config['output_dir'], 'DATA.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data_output, f, indent=2, ensure_ascii=False, default=str)
    print(f"  ✅ DATA.json")


# ==============================================================================
# MAIN
# ==============================================================================

def main(config_path: str = None):
    print("=" * 70)
    print("  COMMUNICATION ANALYSIS TOOLKIT — Analysis Engine")
    print("=" * 70)

    if config_path:
        config = load_config(config_path)
    else:
        config = DEFAULT_CONFIG.copy()
        config['output_dir'] = './output'
        os.makedirs(config['output_dir'], exist_ok=True)

    print(f"\n📋 Case: {config['case_name']}")
    print(f"   {config['user_label']} vs. {config['contact_label']}")
    print(f"   Period: {config['date_start']} to {config['date_end']}\n")

    # ── Step 1: Ingest ──
    print("📥 STEP 1: Ingesting data sources...\n")
    sms_msgs = parse_sms(config.get('sms_xml', ''), config)
    phone_calls = parse_calls(config.get('calls_xml', ''), config)
    signal_calls = parse_signal_calls(config.get('signal_db', ''), config)
    signal_sent = parse_json_messages(config.get('signal_sent_json', ''), 'signal_msl')
    manual_msgs = parse_json_messages(config.get('manual_signal_json', ''), 'signal_manual')
    desktop_msgs = parse_json_messages(config.get('signal_desktop_json', ''), 'signal_desktop')
    csv_msgs = parse_csv_messages(config.get('csv_messages', ''))

    all_texts = sorted(sms_msgs + signal_sent + manual_msgs + desktop_msgs + csv_msgs,
                       key=lambda m: m['timestamp'])
    all_calls = sorted(phone_calls + signal_calls, key=lambda m: m['timestamp'])

    print(f"\n📊 Data loaded: {len(all_texts):,} messages, {len(all_calls):,} calls\n")

    # ── Step 2: Analyze ──
    print("🔍 STEP 2: Running analysis...\n")
    days, gaps = analyze_all(config, all_texts, all_calls)

    contact_days = sum(1 for d in days.values() if d['had_contact'])
    total_hurtful = sum(len(days[d]['hurtful']['from_user']) + len(days[d]['hurtful']['from_contact']) for d in days)
    total_patterns = sum(len(days[d]['patterns']['from_user']) + len(days[d]['patterns']['from_contact']) for d in days)
    print(f"  Days analyzed: {len(days)}")
    print(f"  Days with contact: {contact_days}")
    print(f"  Hurtful language instances: {total_hurtful}")
    print(f"  Behavioral pattern instances: {total_patterns}")
    print(f"  Communication gaps: {len(gaps)}\n")

    # ── Step 3: Generate reports ──
    print("📝 STEP 3: Generating reports...\n")
    out = config['output_dir']

    with open(os.path.join(out, 'ANALYSIS.md'), 'w', encoding='utf-8') as f:
        f.write(generate_analysis_report(config, days, gaps))
    print("  ✅ ANALYSIS.md")

    with open(os.path.join(out, 'EVIDENCE.md'), 'w', encoding='utf-8') as f:
        f.write(generate_evidence_report(config, days))
    print("  ✅ EVIDENCE.md")

    with open(os.path.join(out, 'TIMELINE.md'), 'w', encoding='utf-8') as f:
        f.write(generate_timeline(config, days, gaps))
    print("  ✅ TIMELINE.md")

    with open(os.path.join(out, 'AI_PROMPTS.md'), 'w', encoding='utf-8') as f:
        f.write(generate_ai_prompts(config))
    print("  ✅ AI_PROMPTS.md")

    save_data_json(config, days, gaps)

    print(f"\n{'=' * 70}")
    print(f"  ✅ ALL REPORTS SAVED TO: {out}")
    print(f"{'=' * 70}")


_CONSENT_TEXT = """
╔══════════════════════════════════════════════════════════════════════╗
║                     IMPORTANT LEGAL NOTICE                         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  This tool analyzes personal communication data. Before running:   ║
║                                                                    ║
║  1. You must have LEGAL AUTHORITY to analyze this data.            ║
║     (Your own messages, or data you have legal access to.)         ║
║                                                                    ║
║  2. This tool does NOT produce legally admissible evidence.        ║
║     Output is probabilistic pattern detection, not forensic proof. ║
║                                                                    ║
║  3. Consult an attorney before relying on any analysis in legal    ║
║     proceedings (custody, divorce, restraining orders, etc.).      ║
║                                                                    ║
║  4. Pattern detection can produce false positives and false        ║
║     negatives. Always review flagged content in full context.      ║
║                                                                    ║
║  5. This is NOT a diagnostic tool and does NOT replace clinical    ║
║     or legal professional advice.                                  ║
║                                                                    ║
║  6. Supportive pattern scores analyze TEXT ONLY. Acts of service,  ║
║     quality time, physical affection, and non-verbal cues are NOT  ║
║     captured. A low supportive score does not mean support is      ║
║     absent — it may be expressed through actions, not words.       ║
║                                                                    ║
║  7. "Supportive" text can be manipulative in context (e.g., love  ║
║     bombing). "Negative" text can be reactive self-defense by a   ║
║     victim. Context matters — always consult a professional.       ║
║                                                                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""


def _check_consent(skip: bool = False) -> bool:
    """Display legal notice and obtain user consent on first run.

    Consent is stored in a .consent file in the project root so the
    prompt only appears once. Pass skip=True (or --yes on CLI) to
    bypass for automated/CI runs.
    """
    if skip:
        return True

    consent_file = os.path.join(os.path.dirname(__file__), '..', '.consent')
    consent_file = os.path.realpath(consent_file)
    if os.path.exists(consent_file):
        return True

    print(_CONSENT_TEXT)
    try:
        answer = input("Do you confirm you have legal authority to analyze "
                       "this data? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return False

    if answer in ('y', 'yes'):
        try:
            with open(consent_file, 'w') as f:
                f.write(f"Consent given: {datetime.now().isoformat()}\n")
        except OSError:
            pass  # Non-critical — consent will be asked again next time
        return True

    print("\nYou must confirm consent before running the analysis.")
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Communication Analysis Toolkit')
    parser.add_argument('--config', type=str, help='Path to case config.json')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip consent prompt (for automated/CI use)')
    args = parser.parse_args()

    if not _check_consent(skip=args.yes):
        sys.exit(1)

    main(args.config)
