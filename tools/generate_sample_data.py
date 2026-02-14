"""
================================================================================
Communication Analysis Toolkit — Sample Data Generator
================================================================================

Generates a realistic DATA.json with message-level labels for testing
the dashboard and AI agent. Covers diverse scenarios:
- Normal days, conflict days, silent treatment, reconciliation
- Multiple pattern types (DARVO, gaslighting, stonewalling, etc.)
- Mixed severity levels
- Communication gaps
- Apologies (genuine and dismissive)

Usage:
    python -m tools.generate_sample_data [--output cases/sample/output]
================================================================================
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from engine import logger as engine_logger

# Initialize logger
log = engine_logger.setup_logging(json_output=False, verbose=True)

# ---------------------------------------------------------------------------
# Message templates by scenario
# ---------------------------------------------------------------------------

NORMAL_MESSAGES_USER = [
    "Hey how's your day going?",
    "Want to grab dinner tonight?",
    "I miss you",
    "Just got home from work",
    "That movie was really good!",
    "Can you pick up milk?",
    "Love you ❤️",
    "How was your meeting?",
    "I'll be home around 6",
    "Good morning 😊",
    "Thinking about you",
    "Did you see that sunset?",
    "Can we talk later? Having a busy day",
    "That's so funny lol",
    "I'm proud of you for that presentation",
    "Do you want pizza or Thai?",
    "I had a rough day but feeling better now",
    "Sweet dreams ❤️",
    "Thanks for being understanding",
    "You looked beautiful today",
]

NORMAL_MESSAGES_CONTACT = [
    "Pretty good! Yours?",
    "Sure! Where do you want to go?",
    "Miss you too!",
    "Welcome home!",
    "I know right? So good",
    "Yeah I'll stop by the store",
    "Love you too ❤️",
    "It went well actually!",
    "Ok see you then!",
    "Good morning!",
    "Aw that's sweet",
    "It was gorgeous!",
    "No worries take your time",
    "Haha right??",
    "Thank you! I was so nervous",
    "Thai sounds amazing",
    "I'm sorry you had a rough day",
    "Goodnight ❤️",
    "Always",
    "Stop you're making me blush",
]

# Hurtful messages with expected labels
HURTFUL_CONTACT = [
    {"body": "You're so stupid sometimes I can't even deal with you",
     "words": ["stupid"], "severity": "moderate", "patterns": []},
    {"body": "Nobody else would put up with your shit",
     "words": ["shit"], "severity": "moderate", "patterns": ["isolation_threat"]},
    {"body": "I never said that, you're making things up again",
     "words": ["making things up"], "severity": "moderate", "patterns": ["gaslighting", "deny"]},
    {"body": "Oh so NOW I'm the bad guy? After everything YOU did to me?",
     "words": [], "severity": "moderate", "patterns": ["darvo", "reverse_victim"]},
    {"body": "You're crazy, that literally never happened",
     "words": ["crazy"], "severity": "moderate", "patterns": ["gaslighting"]},
    {"body": "Fine. Whatever. I'm done talking about this.",
     "words": ["whatever"], "severity": "mild", "patterns": ["stonewalling"]},
    {"body": "If you really loved me you wouldn't do this",
     "words": [], "severity": "moderate", "patterns": ["guilt_trip"]},
    {"body": "You always do this. You ALWAYS ruin everything.",
     "words": ["ruin everything"], "severity": "moderate", "patterns": ["gottman_criticism"]},
    {"body": "I can't believe I'm dating someone this pathetic",
     "words": ["pathetic"], "severity": "severe", "patterns": ["gottman_contempt"]},
    {"body": "lol ok sure keep telling yourself that",
     "words": [], "severity": "mild", "patterns": ["gottman_contempt", "minimizing"]},
    {"body": "My ex would never have acted like this",
     "words": [], "severity": "moderate", "patterns": ["triangulation"]},
    {"body": "I'll change I promise, things will be different this time",
     "words": [], "severity": "mild", "patterns": ["future_faking"]},
    {"body": "You're the one who started all of this, not me",
     "words": [], "severity": "moderate", "patterns": ["deflection", "blame_shifting"]},
    {"body": "I didn't mean it like that, you're too sensitive",
     "words": ["too sensitive"], "severity": "moderate", "patterns": ["minimizing", "gaslighting"]},
    {"body": "Don't talk to me. I need space. Don't text me.",
     "words": [], "severity": "mild", "patterns": ["silent_treatment_threat"]},
    {"body": "You're lucky I even put up with you",
     "words": ["lucky I even put up with you"], "severity": "moderate", "patterns": ["coercive_control"]},
    {"body": "Go ahead and cry about it, see if I care",
     "words": ["see if I care"], "severity": "moderate", "patterns": ["gottman_contempt"]},
    {"body": "That's not what happened and you know it",
     "words": [], "severity": "mild", "patterns": ["gaslighting", "deny"]},
    {"body": "You're overreacting as usual",
     "words": ["overreacting"], "severity": "moderate", "patterns": ["minimizing"]},
    {"body": "Maybe if you weren't so insecure we wouldn't have these problems",
     "words": ["insecure"], "severity": "moderate", "patterns": ["deflection"]},
]

HURTFUL_USER = [
    {"body": "This is bullshit and you know it",
     "words": ["bullshit"], "severity": "mild", "patterns": []},
    {"body": "You're being really unfair right now",
     "words": [], "severity": "mild", "patterns": []},
    {"body": "I can't keep doing this",
     "words": [], "severity": "mild", "patterns": []},
    {"body": "Leave me alone right now",
     "words": [], "severity": "mild", "patterns": []},
    {"body": "That's such a lie",
     "words": ["lie"], "severity": "mild", "patterns": []},
]

APOLOGY_GENUINE = [
    {"body": "I shouldn't have said that. I was wrong and I'm sorry.",
     "is_genuine": True},
    {"body": "I need to work on how I react. That wasn't okay.",
     "is_genuine": True},
    {"body": "You deserve better than how I treated you today. I'm truly sorry.",
     "is_genuine": True},
]

APOLOGY_DISMISSIVE = [
    {"body": "Sorry ok? Can we just drop it now?",
     "is_genuine": False, "patterns": ["minimizing"]},
    {"body": "I said I'm sorry what more do you want from me",
     "is_genuine": False, "patterns": ["deflection"]},
    {"body": "Fine I'm sorry. Happy now?",
     "is_genuine": False, "patterns": ["gottman_contempt"]},
]

DE_ESCALATION = [
    "Can we please just talk about this calmly?",
    "I don't want to fight",
    "I hear what you're saying",
    "Let's take a break and come back to this",
    "I love you and I want to work this out",
]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def _random_time(hour_min: int = 7, hour_max: int = 23) -> str:
    h = random.randint(hour_min, hour_max)
    m = random.randint(0, 59)
    return f"{h:02d}:{m:02d}"


def _generate_day(
    date: datetime,
    scenario: str,
) -> dict:
    """Generate a single day's data based on a scenario type."""
    date_str = date.strftime("%Y-%m-%d")
    weekday = date.strftime("%A")

    day: dict = {
        "weekday": weekday,
        "had_contact": scenario != "no_contact",
        "messages_sent": 0,
        "messages_received": 0,
        "calls_in": 0,
        "calls_out": 0,
        "calls_missed": 0,
        "talk_seconds": 0,
        "hurtful_from_user": [],
        "hurtful_from_contact": [],
        "patterns_from_user": [],
        "patterns_from_contact": [],
        "messages": [],  # <-- NEW: full message-level data with labels
    }

    if scenario == "no_contact":
        return day

    msgs = []

    if scenario == "normal":
        # 5-15 messages each way
        n = random.randint(5, 15)
        for _ in range(n):
            t = _random_time()
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "user→contact",
                "body": random.choice(NORMAL_MESSAGES_USER),
                "labels": {"patterns": [], "severity": None, "hurtful_words": [],
                           "is_apology": False, "is_de_escalation": False},
            })
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "contact→user",
                "body": random.choice(NORMAL_MESSAGES_CONTACT),
                "labels": {"patterns": [], "severity": None, "hurtful_words": [],
                           "is_apology": False, "is_de_escalation": False},
            })
        day["messages_sent"] = n
        day["messages_received"] = n
        # Maybe a call
        if random.random() > 0.6:
            day["calls_out"] = 1
            day["talk_seconds"] = random.randint(60, 600)

    elif scenario == "conflict":
        # Normal messages then escalation
        n_normal = random.randint(3, 6)
        for _ in range(n_normal):
            t = _random_time(8, 14)
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "user→contact",
                "body": random.choice(NORMAL_MESSAGES_USER),
                "labels": {"patterns": [], "severity": None, "hurtful_words": [],
                           "is_apology": False, "is_de_escalation": False},
            })
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "contact→user",
                "body": random.choice(NORMAL_MESSAGES_CONTACT),
                "labels": {"patterns": [], "severity": None, "hurtful_words": [],
                           "is_apology": False, "is_de_escalation": False},
            })

        # Hurtful messages from contact (2-5)
        n_hurtful = random.randint(2, 5)
        selected = random.sample(HURTFUL_CONTACT, min(n_hurtful, len(HURTFUL_CONTACT)))
        for h in selected:
            t = _random_time(15, 22)
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "contact→user",
                "body": h["body"],
                "labels": {
                    "patterns": h["patterns"],
                    "severity": h["severity"],
                    "hurtful_words": h["words"],
                    "is_apology": False,
                    "is_de_escalation": False,
                },
            })
            day["hurtful_from_contact"].append({
                "time": f"{date_str} {t}",
                "words": h["words"],
                "severity": h["severity"],
                "preview": h["body"][:80],
                "source": "sms",
            })
            for p in h["patterns"]:
                day["patterns_from_contact"].append({
                    "time": f"{date_str} {t}",
                    "pattern": p,
                    "matched": h["body"][:40],
                    "message": h["body"],
                    "source": "sms",
                })

        # User responses (some hurtful, some de-escalation)
        if random.random() > 0.5:
            hu = random.choice(HURTFUL_USER)
            t = _random_time(15, 22)
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "user→contact",
                "body": hu["body"],
                "labels": {
                    "patterns": hu["patterns"],
                    "severity": hu["severity"],
                    "hurtful_words": hu["words"],
                    "is_apology": False,
                    "is_de_escalation": False,
                },
            })
            day["hurtful_from_user"].append({
                "time": f"{date_str} {t}",
                "words": hu["words"],
                "severity": hu["severity"],
                "preview": hu["body"][:80],
                "source": "sms",
            })

        # De-escalation attempt from user
        t = _random_time(16, 23)
        de_msg = random.choice(DE_ESCALATION)
        msgs.append({
            "time": f"{date_str} {t}",
            "direction": "user→contact",
            "body": de_msg,
            "labels": {
                "patterns": [], "severity": None, "hurtful_words": [],
                "is_apology": False, "is_de_escalation": True,
            },
        })

        day["messages_sent"] = n_normal + 2
        day["messages_received"] = n_normal + n_hurtful

    elif scenario == "reconciliation":
        # Apology + normal messages
        t = _random_time(9, 12)
        apology = random.choice(APOLOGY_GENUINE)
        msgs.append({
            "time": f"{date_str} {t}",
            "direction": "contact→user",
            "body": apology["body"],
            "labels": {
                "patterns": [], "severity": None, "hurtful_words": [],
                "is_apology": True, "is_de_escalation": True,
            },
        })

        n = random.randint(4, 8)
        for _ in range(n):
            t = _random_time(12, 22)
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "user→contact",
                "body": random.choice(NORMAL_MESSAGES_USER),
                "labels": {"patterns": [], "severity": None, "hurtful_words": [],
                           "is_apology": False, "is_de_escalation": False},
            })
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "contact→user",
                "body": random.choice(NORMAL_MESSAGES_CONTACT),
                "labels": {"patterns": [], "severity": None, "hurtful_words": [],
                           "is_apology": False, "is_de_escalation": False},
            })
        day["messages_sent"] = n
        day["messages_received"] = n + 1

    elif scenario == "dismissive_apology":
        t = _random_time(10, 14)
        apology = random.choice(APOLOGY_DISMISSIVE)
        msgs.append({
            "time": f"{date_str} {t}",
            "direction": "contact→user",
            "body": apology["body"],
            "labels": {
                "patterns": apology.get("patterns", []),
                "severity": "mild",
                "hurtful_words": [],
                "is_apology": False,  # Not genuinely apologetic
                "is_de_escalation": False,
            },
        })
        for p in apology.get("patterns", []):
            day["patterns_from_contact"].append({
                "time": f"{date_str} {t}",
                "pattern": p,
                "matched": apology["body"][:40],
                "message": apology["body"],
                "source": "sms",
            })
        day["messages_sent"] = 2
        day["messages_received"] = 3

    elif scenario == "love_bombing":
        # Excessive affection after conflict
        love_msgs = [
            "You're the most amazing person in the world",
            "I don't deserve someone as perfect as you",
            "I'll do anything for you, you know that right?",
            "Nobody will ever love you like I do",
            "You complete me, I'm nothing without you",
            "Let me buy you that thing you wanted",
            "I was thinking we should go on a trip together",
        ]
        for body in random.sample(love_msgs, min(5, len(love_msgs))):
            t = _random_time()
            is_love_bomb = "nobody" in body.lower() or "nothing without" in body.lower()
            msgs.append({
                "time": f"{date_str} {t}",
                "direction": "contact→user",
                "body": body,
                "labels": {
                    "patterns": ["love_bombing"] if is_love_bomb else [],
                    "severity": "mild" if is_love_bomb else None,
                    "hurtful_words": [],
                    "is_apology": False, "is_de_escalation": False,
                },
            })
            if is_love_bomb:
                day["patterns_from_contact"].append({
                    "time": f"{date_str} {t}",
                    "pattern": "love_bombing",
                    "matched": body[:40],
                    "message": body,
                    "source": "sms",
                })
        day["messages_sent"] = 3
        day["messages_received"] = 5

    # Sort messages by time
    msgs.sort(key=lambda m: m["time"])
    day["messages"] = msgs

    return day


def generate_sample_data(output_dir: str = "cases/sample/output") -> Path:
    """Generate a complete sample DATA.json."""
    random.seed(42)  # Reproducible

    # 90-day period
    start = datetime(2025, 6, 1)
    end = datetime(2025, 8, 29)

    # Scenario distribution across 90 days
    # Realistic pattern: mostly normal, periodic conflict, gaps
    scenarios = []
    day = start
    while day <= end:
        r = random.random()
        if r < 0.45:
            scenarios.append("normal")
        elif r < 0.65:
            scenarios.append("conflict")
        elif r < 0.75:
            scenarios.append("no_contact")
        elif r < 0.82:
            scenarios.append("reconciliation")
        elif r < 0.88:
            scenarios.append("dismissive_apology")
        elif r < 0.93:
            scenarios.append("love_bombing")
        else:
            scenarios.append("no_contact")
        day += timedelta(days=1)

    # Generate days
    days: dict[str, dict] = {}
    current = start
    for i, scenario in enumerate(scenarios):
        if current > end:
            break
        days[current.strftime("%Y-%m-%d")] = _generate_day(current, scenario)
        current += timedelta(days=1)

    # Find communication gaps (3+ consecutive no-contact days)
    gaps = []
    sorted_dates = sorted(days.keys())
    gap_start = None
    gap_days = 0
    for d in sorted_dates:
        if not days[d]["had_contact"]:
            if gap_start is None:
                gap_start = d
            gap_days += 1
        else:
            if gap_start and gap_days >= 3:
                gaps.append({
                    "start": gap_start,
                    "end": d,
                    "days": gap_days,
                    "reason": random.choice([
                        "No communication detected",
                        "Possible silent treatment period",
                        "Extended break in contact",
                    ]),
                })
            gap_start = None
            gap_days = 0

    data = {
        "case": "Sample Analysis",
        "user": "Alex",
        "contact": "Jordan",
        "period": {
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
        },
        "generated": datetime.now().isoformat(),
        "days": days,
        "gaps": gaps,
    }

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    data_path = out_path / "DATA.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Log summary
    total_days = len(days)
    contact_days = sum(1 for d in days.values() if d["had_contact"])
    total_msgs = sum(len(d.get("messages", [])) for d in days.values())
    total_hurtful = sum(
        len(d.get("hurtful_from_contact", [])) + len(d.get("hurtful_from_user", []))
        for d in days.values()
    )
    total_patterns = sum(
        len(d.get("patterns_from_contact", [])) + len(d.get("patterns_from_user", []))
        for d in days.values()
    )

    log.info("sample_data_generated",
             path=str(data_path),
             total_days=total_days,
             contact_days=contact_days,
             total_messages=total_msgs,
             total_hurtful=total_hurtful,
             total_patterns=total_patterns,
             communication_gaps=len(gaps))

    return data_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "cases/sample/output"
    generate_sample_data(out)
