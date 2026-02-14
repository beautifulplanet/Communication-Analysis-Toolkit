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

import os
from datetime import datetime, timedelta
from typing import Any, Optional

from engine.config import DEFAULT_CONFIG, load_config

# ==============================================================================
# DATA INGESTION
# ==============================================================================
from engine.ingestion import (
    parse_calls,
    parse_csv_messages,
    parse_json_messages,
    parse_signal_calls,
    parse_sms,
)
from engine.logger import logger
from engine.patterns import (
    detect_patterns,
    is_directed_hurtful,
)
from engine.patterns_supportive import (
    detect_supportive_patterns,
)
from engine.reporting import (
    generate_ai_prompts,
    generate_analysis_report,
    generate_evidence_report,
    generate_timeline,
    save_data_json,
)
from engine.types import CallDict, DayData, GapData, HurtfulEntry, MessageDict, PatternEntry
from engine.db import init_db
from engine.storage import CaseStorage
from pathlib import Path

# ==============================================================================
# ANALYSIS ENGINE
# ==============================================================================


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


def analyze_all(
    config: dict[str, Any], all_texts: list[MessageDict], all_calls: list[CallDict]
) -> tuple[dict[str, DayData], list[GapData]]:
    """Run all analysis on the combined data."""
    start = datetime.strptime(config["date_start"], "%Y-%m-%d")
    end = datetime.strptime(config["date_end"], "%Y-%m-%d")

    # Build daily data structure
    days: dict[str, DayData] = {}
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        days[date_str] = {
            "date": date_str,
            "weekday": current.strftime("%A"),
            "had_contact": False,
            "messages": {"sent": 0, "received": 0, "all": []},
            "calls": {"incoming": 0, "outgoing": 0, "missed": 0, "total_seconds": 0},
            "hurtful": {"from_user": [], "from_contact": []},
            "patterns": {"from_user": [], "from_contact": []},
            "supportive": {"from_user": [], "from_contact": []},
        }
        current += timedelta(days=1)

    # Populate messages
    for msg in all_texts:
        d = msg["date"]
        if d not in days:
            continue
        days[d]["had_contact"] = True
        if msg["direction"] == "sent":
            days[d]["messages"]["sent"] += 1
        else:
            days[d]["messages"]["received"] += 1
        days[d]["messages"]["all"].append(msg)

        # Hurtful language check
        is_h, words, sev = is_directed_hurtful(msg.get("body", ""), msg["direction"])
        if is_h:
            h_entry: HurtfulEntry = {
                "time": msg["time"],
                "words": words,
                "severity": sev or "unknown",
                "preview": (msg.get("body", "")[:150] + "...")
                if len(msg.get("body", "")) > 150
                else msg.get("body", ""),
                "source": msg.get("source", "unknown"),
            }
            if msg["direction"] == "sent":
                days[d]["hurtful"]["from_user"].append(h_entry)
            else:
                days[d]["hurtful"]["from_contact"].append(h_entry)

        # Pattern detection
        pattern_results = detect_patterns(msg.get("body", ""), msg["direction"])
        if pattern_results:
            for pattern_type, matched, full_msg in pattern_results:
                p_entry: PatternEntry = {
                    "time": msg["time"],
                    "pattern": pattern_type,
                    "matched": matched,
                    "message": (full_msg[:200] + "...") if len(full_msg) > 200 else full_msg,
                    "source": msg.get("source", "unknown"),
                }
                if msg["direction"] == "sent":
                    days[d]["patterns"]["from_user"].append(p_entry)
                else:
                    days[d]["patterns"]["from_contact"].append(p_entry)

        # Supportive pattern detection
        supportive_results = detect_supportive_patterns(msg.get("body", ""), msg["direction"])
        if supportive_results:
            for pattern_type, matched, full_msg in supportive_results:
                entry = {
                    "time": msg["time"],
                    "pattern": pattern_type,
                    "matched": matched,
                    "message": (full_msg[:200] + "...") if len(full_msg) > 200 else full_msg,
                    "source": msg.get("source", "unknown"),
                }
                if msg["direction"] == "sent":
                    days[d]["supportive"]["from_user"].append(entry)
                else:
                    days[d]["supportive"]["from_contact"].append(entry)

    # Populate calls
    for call in all_calls:
        d = call["date"]
        if d not in days:
            continue
        days[d]["had_contact"] = True
        direction = call.get("direction", "")
        if direction in ("incoming", "accepted"):
            days[d]["calls"]["incoming"] += 1
        elif direction == "outgoing":
            days[d]["calls"]["outgoing"] += 1
        elif direction in ("missed", "not_accepted", "declined", "rejected"):
            days[d]["calls"]["missed"] += 1
        days[d]["calls"]["total_seconds"] += call.get("duration", 0)

    # Identify communication gaps
    sorted_dates = sorted(days.keys())
    contact_dates = [d for d in sorted_dates if days[d]["had_contact"]]

    gaps: list[GapData] = []
    for i in range(len(contact_dates) - 1):
        d1 = datetime.strptime(contact_dates[i], "%Y-%m-%d")
        d2 = datetime.strptime(contact_dates[i + 1], "%Y-%m-%d")
        gap_days = (d2 - d1).days - 1
        if gap_days >= 3:
            prev_day = days[contact_dates[i]]
            was_heated = (
                len(prev_day["hurtful"]["from_user"]) + len(prev_day["hurtful"]["from_contact"]) > 0
            )
            reason = "After conflict" if was_heated else "Unknown"
            gaps.append(
                {
                    "start": (d1 + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "end": (d2 - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "days": gap_days,
                    "reason": reason,
                }
            )
    gaps.sort(key=lambda g: g["days"], reverse=True)

    return days, gaps


# ==============================================================================
# REPORT GENERATION
# ==============================================================================



# ==============================================================================
# MAIN
# ==============================================================================


def run_analysis(config_path: Optional[str] = None, use_db: bool = False) -> None:
    logger.info("analysis_started")

    if config_path:
        config = load_config(config_path)
    else:
        config = DEFAULT_CONFIG.copy()
        config["output_dir"] = "./output"
        os.makedirs(config["output_dir"], exist_ok=True)

    logger.info(
        "case_loaded",
        case=config["case_name"],
        user=config["user_label"],
        contact=config["contact_label"],
        period_start=config["date_start"],
        period_end=config["date_end"],
    )

    # ── Step 1: Ingest ──
    logger.info("ingestion_started")
    sms_msgs = parse_sms(config.get("sms_xml", ""), config)
    phone_calls = parse_calls(config.get("calls_xml", ""), config)
    signal_calls = parse_signal_calls(config.get("signal_db", ""), config)
    signal_sent = parse_json_messages(config.get("signal_sent_json", ""), "signal_msl")
    manual_msgs = parse_json_messages(config.get("manual_signal_json", ""), "signal_manual")
    desktop_msgs = parse_json_messages(config.get("signal_desktop_json", ""), "signal_desktop")
    csv_msgs = parse_csv_messages(config.get("csv_messages", ""))

    from typing import cast

    all_texts = cast(
        list[MessageDict],
        sorted(
            sms_msgs + signal_sent + manual_msgs + desktop_msgs + csv_msgs,
            key=lambda m: m["timestamp"],
        ),
    )
    all_calls = cast(
        list[CallDict], sorted(phone_calls + signal_calls, key=lambda m: m["timestamp"])
    )

    logger.info("data_loaded", message_count=len(all_texts), call_count=len(all_calls))
    
    # ── DB Ingestion ──
    if use_db:
        db_path = Path(config["output_dir"]) / "cases.db"
        logger.info("db_ingestion_started", db_path=str(db_path))
        
        init_db(db_path)
        store = CaseStorage(db_path)
        
        case_id = store.create_case(
            name=config["case_name"],
            user_name=config["user_label"],
            contact_name=config["contact_label"],
            source_path=config_path or "manual_config"
        )
        
        # Optimization: In the future, we can use a transaction here.
        # For now, relying on CaseStorage's internal connection management.
        
        count = 0 
        for msg in all_texts:
            store.add_message(case_id, msg)
            count += 1
            
        logger.info("db_ingestion_complete", inserted_messages=count)

    # ── Step 2: Analyze ──
    # ── Step 2: Analyze ──
    logger.info("analysis_started")
    days, gaps = analyze_all(config, all_texts, all_calls)

    contact_days = sum(1 for d in days.values() if d["had_contact"])
    total_hurtful = sum(
        len(days[d]["hurtful"]["from_user"]) + len(days[d]["hurtful"]["from_contact"]) for d in days
    )
    total_patterns = sum(
        len(days[d]["patterns"]["from_user"]) + len(days[d]["patterns"]["from_contact"])
        for d in days
    )

    logger.info(
        "analysis_complete",
        days_analyzed=len(days),
        days_with_contact=contact_days,
        hurtful_instances=total_hurtful,
        pattern_instances=total_patterns,
        gaps_found=len(gaps),
    )

    # ── Step 3: Generate reports ──
    logger.info("writing_reports", output_dir=config["output_dir"])
    out = config["output_dir"]

    with open(os.path.join(out, "ANALYSIS.md"), "w", encoding="utf-8") as f:
        f.write(generate_analysis_report(config, days, gaps))
    logger.info("report_saved", file="ANALYSIS.md")

    with open(os.path.join(out, "EVIDENCE.md"), "w", encoding="utf-8") as f:
        f.write(generate_evidence_report(config, days))
    logger.info("report_saved", file="EVIDENCE.md")

    with open(os.path.join(out, "TIMELINE.md"), "w", encoding="utf-8") as f:
        f.write(generate_timeline(config, days, gaps))
    logger.info("report_saved", file="TIMELINE.md")

    with open(os.path.join(out, "AI_PROMPTS.md"), "w", encoding="utf-8") as f:
        f.write(generate_ai_prompts(config))
    logger.info("report_saved", file="AI_PROMPTS.md")

    save_data_json(config, days, gaps)

    logger.info("all_reports_saved", directory=out)


    save_data_json(config, days, gaps)

    logger.info("all_reports_saved", directory=out)


if __name__ == "__main__":
    import argparse
    import sys
    from engine.db import init_db
    from engine.storage import CaseStorage
    
    parser = argparse.ArgumentParser(description="Communication Analysis Toolkit")
    parser.add_argument("--config", help="Path to config.json")
    parser.add_argument("--use-db", action="store_true", help="Use SQLite database for storage")
    args = parser.parse_args()
    
    try:
        # If --use-db is set, we need to pass this down or handle it here.
        # Since run_analysis currently only takes config_path, best to refactor 
        # run_analysis to accept kwargs or modify it. 
        # For now, let's modify run_analysis signature in the next step, 
        # and just pass the flag here.
        run_analysis(args.config, use_db=args.use_db)
    except Exception as e:
        logger.error("analysis_failed", error=str(e))
        sys.exit(1)
