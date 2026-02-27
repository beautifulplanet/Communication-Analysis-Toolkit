"""
================================================================================
Communication Analysis Toolkit — Reporting Module
================================================================================

Generates all output reports:
  - ANALYSIS.md       — Comprehensive statistics & pattern summary
  - EVIDENCE.md       — Verified pattern instances with full quotes
  - TIMELINE.md       — Day-by-day narrative timeline
  - AI_PROMPTS.md     — Prompts for external AI auditing
  - DATA.json         — Machine-readable full dataset

Extracted from analyzer.py for cleaner separation of concerns.
================================================================================
"""

import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Any

from engine.config import escape_md
from engine.crypto import encrypt_data
from engine.logger import logger
from engine.patterns import (
    PATTERN_DESCRIPTIONS,
    PATTERN_LABELS,
    PATTERN_SEVERITY,
)
from engine.types import DayData, GapData, HurtfulEntryWithDate, PatternEntryWithDate


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


def generate_analysis_report(
    config: dict[str, Any], days: dict[str, DayData], gaps: list[GapData]
) -> str:
    """Generate ANALYSIS.md — comprehensive statistics."""
    user = escape_md(config["user_label"])
    contact = escape_md(config["contact_label"])
    case_name = escape_md(config["case_name"])
    sorted_dates = sorted(days.keys())
    contact_days = [d for d in sorted_dates if days[d]["had_contact"]]
    no_contact = [d for d in sorted_dates if not days[d]["had_contact"]]

    total_sent = sum(days[d]["messages"]["sent"] for d in sorted_dates)
    total_received = sum(days[d]["messages"]["received"] for d in sorted_dates)
    total_calls = sum(
        days[d]["calls"]["incoming"] + days[d]["calls"]["outgoing"] + days[d]["calls"]["missed"]
        for d in sorted_dates
    )
    total_talk = sum(days[d]["calls"]["total_seconds"] for d in sorted_dates)

    total_hurtful_user = sum(len(days[d]["hurtful"]["from_user"]) for d in sorted_dates)
    total_hurtful_contact = sum(len(days[d]["hurtful"]["from_contact"]) for d in sorted_dates)

    # Severity breakdowns
    h_user_severe = sum(
        1
        for d in sorted_dates
        for h in days[d]["hurtful"]["from_user"]
        if h["severity"] == "severe"
    )
    h_contact_severe = sum(
        1
        for d in sorted_dates
        for h in days[d]["hurtful"]["from_contact"]
        if h["severity"] == "severe"
    )
    h_user_moderate = sum(
        1
        for d in sorted_dates
        for h in days[d]["hurtful"]["from_user"]
        if h["severity"] == "moderate"
    )
    h_contact_moderate = sum(
        1
        for d in sorted_dates
        for h in days[d]["hurtful"]["from_contact"]
        if h["severity"] == "moderate"
    )
    h_user_mild = sum(
        1 for d in sorted_dates for h in days[d]["hurtful"]["from_user"] if h["severity"] == "mild"
    )
    h_contact_mild = sum(
        1
        for d in sorted_dates
        for h in days[d]["hurtful"]["from_contact"]
        if h["severity"] == "mild"
    )

    # Pattern counts
    patterns_user: dict[str, int] = defaultdict(int)
    patterns_contact: dict[str, int] = defaultdict(int)
    for d in sorted_dates:
        for entry in days[d]["patterns"]["from_user"]:
            patterns_user[entry["pattern"]] += 1
        for entry in days[d]["patterns"]["from_contact"]:
            patterns_contact[entry["pattern"]] += 1

    lines = []
    lines.append("# Communication Analysis\n")
    lines.append(f"**Case**: {case_name}")
    lines.append(f"**Parties**: {user} (analyzed user) vs. {contact}")
    lines.append(
        f"**Analysis Period**: {config['date_start']} to {config['date_end']} ({len(sorted_dates)} days)"
    )
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")

    lines.append("## Executive Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Days Analyzed | {len(sorted_dates)} |")
    lines.append(
        f"| Days WITH Contact | {len(contact_days)} ({100 * len(contact_days) // max(len(sorted_dates), 1)}%) |"
    )
    lines.append(
        f"| Days WITHOUT Contact | {len(no_contact)} ({100 * len(no_contact) // max(len(sorted_dates), 1)}%) |"
    )
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
    lines.append(
        "*Patterns detected using behavioral science taxonomy (DARVO, Gottman, Coercive Control, etc.)*\n"
    )
    all_patterns = sorted(
        set(list(patterns_user.keys()) + list(patterns_contact.keys())),
        key=lambda p: PATTERN_SEVERITY.get(p, 0),
        reverse=True,
    )
    if all_patterns:
        lines.append(f"| Pattern | {user} | {contact} | Source |")
        lines.append("|---------|--------|---------|--------|")
        for p in all_patterns:
            label = PATTERN_LABELS.get(p, p)
            desc = PATTERN_DESCRIPTIONS.get(p, "")
            source = desc.split("(")[-1].rstrip(")") if "(" in desc else ""
            lines.append(
                f"| {label} | {patterns_user.get(p, 0)} | {patterns_contact.get(p, 0)} | {source} |"
            )
        lines.append(
            f"| **Total** | **{sum(patterns_user.values())}** | **{sum(patterns_contact.values())}** | |"
        )
    lines.append("")

    # Communication gaps
    lines.append("## Communication Gaps (3+ days)\n")
    lines.append("| Start | End | Days Silent | Reason |")
    lines.append("|-------|-----|-------------|--------|")
    for gap in gaps[:25]:
        lines.append(f"| {gap['start']} | {gap['end']} | **{gap['days']}** | {gap['reason']} |")
    lines.append("")

    return "\n".join(lines)


def generate_evidence_report(config: dict[str, Any], days: dict[str, DayData]) -> str:
    """Generate EVIDENCE.md — verified manipulation instances with full quotes."""
    user = escape_md(config["user_label"])
    contact = escape_md(config["contact_label"])
    sorted_dates = sorted(days.keys())

    lines = []
    lines.append("# Verified Behavioral Pattern Evidence\n")
    lines.append(f"**Case**: {escape_md(config['case_name'])}")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("**Method**: Context-aware behavioral pattern detection\n")
    lines.append("---\n")

    lines.append(f"## Hurtful Language FROM {contact}\n")
    all_hurtful_contact: list[HurtfulEntryWithDate] = []
    for d in sorted_dates:
        for h in days[d]["hurtful"]["from_contact"]:
            h_entry_with_date: HurtfulEntryWithDate = {**h, "date": d}
            all_hurtful_contact.append(h_entry_with_date)

    for severity, emoji, desc in [
        ("severe", "🔴", "Personal attacks, weaponizing trauma, threats"),
        ("moderate", "🟠", "Directed insults and profanity"),
        ("mild", "🟡", "Dismissive language, contextual profanity"),
    ]:
        items = [h for h in all_hurtful_contact if h["severity"] == severity]
        if items:
            lines.append(f"### {emoji} {severity.title()} ({len(items)} instances) — {desc}\n")
            for h in items:
                lines.append(
                    f"**{h['date']} {h['time']}** ({h['source'].upper()}) — Flagged: `{', '.join(h['words'])}`"
                )
                lines.append(f"> {escape_md(h['preview'])}\n")

    # Hurtful from user
    lines.append(f"## Hurtful Language FROM {user}\n")
    all_hurtful_user: list[HurtfulEntryWithDate] = []
    for d in sorted_dates:
        for h in days[d]["hurtful"]["from_user"]:
            h_entry_with_date_user: HurtfulEntryWithDate = {**h, "date": d}
            all_hurtful_user.append(h_entry_with_date_user)

    for severity, emoji, desc in [
        ("severe", "🔴", "Personal attacks, weaponizing trauma, threats"),
        ("moderate", "🟠", "Directed insults and profanity"),
        ("mild", "🟡", "Dismissive language, contextual profanity"),
    ]:
        items = [h for h in all_hurtful_user if h["severity"] == severity]
        if items:
            lines.append(f"### {emoji} {severity.title()} ({len(items)} instances) — {desc}\n")
            for h in items:
                lines.append(
                    f"**{h['date']} {h['time']}** ({h['source'].upper()}) — Flagged: `{', '.join(h['words'])}`"
                )
                lines.append(f"> {escape_md(h['preview'])}\n")

    if not all_hurtful_user:
        lines.append(f"*No directed hurtful language detected from {user}.*\n")

    # Patterns from contact
    lines.append("---\n")
    lines.append(f"## Behavioral Patterns FROM {contact}\n")

    all_patterns_contact: list[PatternEntryWithDate] = []
    for d in sorted_dates:
        for entry in days[d]["patterns"]["from_contact"]:
            p_entry_with_date: PatternEntryWithDate = {**entry, "date": d}
            all_patterns_contact.append(p_entry_with_date)

    pattern_order = sorted(
        set(e["pattern"] for e in all_patterns_contact),
        key=lambda p: PATTERN_SEVERITY.get(p, 0),
        reverse=True,
    )

    for pattern in pattern_order:
        pattern_items = [e for e in all_patterns_contact if e["pattern"] == pattern]
        if pattern_items:
            label = PATTERN_LABELS.get(pattern, pattern)
            lines.append(f"### {label} ({len(pattern_items)} instances)\n")
            seen: dict[str, Any] = {}
            for e in pattern_items:
                key = e["message"].strip()[:100]
                if key in seen:
                    seen[key]["count"] += 1
                else:
                    seen[key] = {"entry": e, "count": 1}
            for _key, info in seen.items():
                e = info["entry"]
                count_note = f" x{info['count']}" if info["count"] > 1 else ""
                lines.append(f"**{e['date']} {e['time']}{count_note}** — Matched: `{e['matched']}`")
                lines.append(f"> {escape_md(e['message'])}\n")

    # Patterns from user
    lines.append(f"## Behavioral Patterns FROM {user}\n")
    lines.append(
        f"> Note: Some patterns from {user} may be reactive/defensive rather than manipulative."
    )
    lines.append(
        '> Context matters — a "leave me alone" request during an argument differs from a controlling ultimatum.\n'
    )

    all_patterns_user: list[PatternEntryWithDate] = []
    for d in sorted_dates:
        for entry in days[d]["patterns"]["from_user"]:
            all_patterns_user.append({**entry, "date": d})

    if all_patterns_user:
        pattern_order_user = sorted(
            set(e["pattern"] for e in all_patterns_user),
            key=lambda p: PATTERN_SEVERITY.get(p, 0),
            reverse=True,
        )
        for pattern in pattern_order_user:
            pattern_items_user = [e for e in all_patterns_user if e["pattern"] == pattern]
            if pattern_items_user:
                label = PATTERN_LABELS.get(pattern, pattern)
                lines.append(f"### {label} ({len(pattern_items_user)} instances)\n")
                for e in pattern_items_user:
                    lines.append(f"**{e['date']} {e['time']}** — Matched: `{e['matched']}`")
                    lines.append(f"> {escape_md(e['message'])}\n")
    else:
        lines.append(f"*No manipulation patterns detected from {user}.*\n")

    return "\n".join(lines)


def generate_timeline(config: dict[str, Any], days: dict[str, DayData], gaps: list[GapData]) -> str:
    """Generate TIMELINE.md — narrative day-by-day timeline."""
    user = escape_md(config["user_label"])
    contact = escape_md(config["contact_label"])
    sorted_dates = sorted(days.keys())

    gap_lookup = {}
    for gap in gaps:
        gap_lookup[gap["start"]] = gap

    lines = []
    lines.append("# Communication Timeline\n")
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
            dt = datetime.strptime(d, "%Y-%m-%d")
            lines.append(f"\n## {dt.strftime('%B %Y')}\n")

        if d in gap_lookup and d not in gap_shown:
            gap = gap_lookup[d]
            gap_shown.add(d)
            lines.append(
                f"### 📵 NO CONTACT: {gap['start']} → {gap['end']} ({gap['days']} days) — {gap['reason']}\n"
            )
            continue

        if not day["had_contact"]:
            continue

        total_msgs = day["messages"]["sent"] + day["messages"]["received"]
        total_calls = day["calls"]["incoming"] + day["calls"]["outgoing"] + day["calls"]["missed"]
        talk = (
            format_duration(day["calls"]["total_seconds"])
            if day["calls"]["total_seconds"] > 0
            else ""
        )

        hurtful_count = len(day["hurtful"]["from_user"]) + len(day["hurtful"]["from_contact"])
        pattern_count = len(day["patterns"]["from_user"]) + len(day["patterns"]["from_contact"])

        if hurtful_count >= 3 or any(
            h["severity"] == "severe"
            for h in day["hurtful"]["from_contact"] + day["hurtful"]["from_user"]
        ):
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
        summary = " · ".join(parts) if parts else "Contact"

        lines.append(f"### {d} ({day['weekday']}) {mood}")
        lines.append(f"_{summary}_\n")

        for h in day["hurtful"]["from_contact"]:
            sev_emoji = {"severe": "🔴", "moderate": "🟠", "mild": "🟡"}[h["severity"]]
            lines.append(
                f'- {sev_emoji} **{contact}** [{h["severity"]}]: {", ".join(h["words"])} — *"{escape_md(h["preview"])}"*'
            )

        for h in day["hurtful"]["from_user"]:
            sev_emoji = {"severe": "🔴", "moderate": "🟠", "mild": "🟡"}[h["severity"]]
            lines.append(
                f'- {sev_emoji} **{user}** [{h["severity"]}]: {", ".join(h["words"])} — *"{escape_md(h["preview"])}"*'
            )

        for e in day["patterns"]["from_contact"]:
            label = PATTERN_LABELS.get(e["pattern"], e["pattern"])
            lines.append(f'- ⚠️ **{contact}** [{label}]: *"{escape_md(e["message"])}"*')

        if (
            day["hurtful"]["from_contact"]
            or day["hurtful"]["from_user"]
            or day["patterns"]["from_contact"]
        ):
            lines.append("")

    return "\n".join(lines)


def generate_ai_prompts(config: dict[str, Any]) -> str:
    """Generate AI_PROMPTS.md — prompts for external AI auditing."""
    escape_md(config["user_label"])
    escape_md(config["contact_label"])
    return """# AI Audit Prompts

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
You are a data integrity analyst. Review this communication analysis for:

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
You are a behavioral analysis assistant specializing in communication pattern recognition.
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


def save_data_json(config: dict[str, Any], days: dict[str, DayData], gaps: list[GapData]) -> None:
    """Save machine-readable DATA.json."""
    json_days = {}
    for d, day in days.items():
        json_days[d] = {
            "date": day["date"],
            "weekday": day["weekday"],
            "had_contact": day["had_contact"],
            "messages_sent": day["messages"]["sent"],
            "messages_received": day["messages"]["received"],
            "calls_in": day["calls"]["incoming"],
            "calls_out": day["calls"]["outgoing"],
            "calls_missed": day["calls"]["missed"],
            "talk_seconds": day["calls"]["total_seconds"],
            "hurtful_from_user": day["hurtful"]["from_user"],
            "hurtful_from_contact": day["hurtful"]["from_contact"],
            "patterns_from_user": day["patterns"]["from_user"],
            "patterns_from_contact": day["patterns"]["from_contact"],
        }

    data_output = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "case": config["case_name"],
        "user": config["user_label"],
        "contact": config["contact_label"],
        "period": {"start": config["date_start"], "end": config["date_end"]},
        "days": json_days,
        "gaps": gaps,
    }

    output_path = os.path.join(config["output_dir"], "DATA.json")

    # Serialize to JSON bytes
    json_str = json.dumps(data_output, indent=2, ensure_ascii=False, default=str)
    json_bytes = json_str.encode("utf-8")

    # Encrypt (if key configured)
    final_bytes = encrypt_data(json_bytes)

    # Write binary
    with open(output_path, "wb") as f:
        f.write(final_bytes)
    logger.info("report_saved", file="DATA.json")
