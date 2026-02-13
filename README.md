# Communication Analysis Toolkit

**Version 3.0.0**
.
A clinical-grade analysis engine for text-based communication. Identifies behavioral patterns, communication dynamics, and interaction health using peer-reviewed behavioral science

> **Not a diagnostic tool.** Pattern detection is probabilistic. Always review flagged content in context. This is not a substitute for professional legal or clinical advice.

---

## What It Does

Given communication data (SMS, Signal, CSV, or JSON), this tool produces:

- **TIMELINE.md** — Day-by-day narrative with mood indicators and flagged incidents
- **ANALYSIS.md** — Comprehensive statistics: message volumes, language analysis, pattern breakdowns
- **EVIDENCE.md** — Every flagged incident with full quotes, matched patterns, and severity ratings
- **DATA.json** — Machine-readable dataset for further analysis or visualization
- **AI_PROMPTS.md** — Ready-made prompts for external AI auditing (ChatGPT, Claude, Gemini)

---

## Pattern Detection Categories

All patterns are sourced from peer-reviewed clinical psychology and communication research.

### Core DARVO (Freyd, 1997)
| Pattern | Description |
|---------|-------------|
| Deny | Denying something they clearly did or said |
| Attack | Turning it around to attack the other person |
| Reverse Victim & Offender | Making themselves the victim when they are the offender |

### Gottman's Four Horsemen (Gottman & Silver, 1999)
| Pattern | Description |
|---------|-------------|
| Criticism | Attacking character rather than addressing specific behavior |
| Contempt | Treating with disrespect, mockery, or superiority |
| Defensiveness | Deflecting responsibility and counter-blaming |
| Stonewalling | Withdrawing, shutting down, or refusing to engage |

### Gaslighting (Stern, 2007)
Reality denial, sanity questioning, sensitivity shaming, joke deflection, social consensus weaponizing.

### Coercive Control (Stark, 2007; Duluth Model)
| Pattern | Description |
|---------|-------------|
| Control & Isolation | Controlling who the person sees, talks to, or where they go |
| Financial Control | Using money or finances as leverage |
| Weaponizing Family/Health | Using family illness, death, or trauma as leverage |

### Extended Manipulation
| Pattern | Source |
|---------|--------|
| Guilt Trip | Clinical literature |
| Deflection | Clinical literature |
| Ultimatums & Threats | Bancroft, 2002 |
| Looping / Interrogation | Bancroft, 2002 |
| Lying Indicators | Forensic communication |
| Minimizing | Clinical literature |
| Love Bombing | Arabi, 2017 |
| Future Faking | Clinical literature |
| Triangulation | Clinical literature |
| Emotional Blackmail | Forward & Frazier, 1997 |
| Silent Treatment | Clinical literature |
| Double Bind | Bateson, 1956 |
| Selective Memory | Clinical literature |
| Catastrophizing | CBT literature |
| Demand for Compliance | Clinical literature |

### Hurtful Language (3-Tier Severity)
| Level | Description |
|-------|-------------|
| Severe | Personal attacks, weaponizing trauma, credible threats |
| Moderate | Directed profanity, insults aimed at the person |
| Mild | Dismissive language, contextual profanity |

---

## Context-Aware Filtering (v3.0)

The engine includes **7 context filter functions** that dramatically reduce false positives by recognizing benign intent:

| Filter | What it detects |
|--------|----------------|
| `is_apology` | "I'm sorry", "my bad", "I was wrong" |
| `is_self_directed` | Negativity about self, not the other person |
| `is_third_party_venting` | Complaints about work, boss, traffic — not partner |
| `is_de_escalation` | "Let's calm down", "I don't want to fight" |
| `is_expressing_hurt` | "Sounds like you don't wanna see me" — hurt, not attack |
| `is_joke_context` | Surrounding messages contain laughter/emoji signals |
| `is_banter` | Both sides laughing in a window — playful exchange |

For lower-severity categories (defensiveness, stonewalling, minimizing, etc.), matches are suppressed when any context filter fires. High-severity categories (control, gaslighting, emotional blackmail) are **never** suppressed.

---

## Quick Start

### 1. Set Up a Case

```
Communication Analysis Toolkit/
├── engine/
│   ├── __init__.py
│   ├── analyzer.py        # Main analysis engine
│   └── patterns.py        # Pattern detection library
├── active/
│   ├── signal_desktop_extractor.py
│   ├── extract_signal_messages.py
│   ├── generate_monthly_reports.py
│   └── parse_manual_messages.py
├── tools/                   # Diagnostic & extraction utilities
├── cases/
│   └── my_case/
│       ├── config.json     # Case configuration
│       ├── source_data/    # Your data files here
│       └── output/         # Generated reports
├── requirements.txt
├── .gitignore
└── README.md
```

### 2. Create config.json

```json
{
    "case_name": "My Case",
    "user_label": "User A",
    "contact_label": "User B",
    "contact_phone": "+1234567890",
    "phone_suffix": "1234567890",
    "sms_xml": "./cases/my_case/source_data/sms_backup.xml",
    "calls_xml": "./cases/my_case/source_data/calls_backup.xml",
    "signal_desktop_json": "./cases/my_case/source_data/signal_messages.json",
    "csv_messages": "./cases/my_case/source_data/messages.csv",
    "output_dir": "./cases/my_case/output",
    "date_start": "2025-01-01",
    "date_end": "2026-02-09"
}
```

### 3. Run the Analysis

```bash
python -m engine.analyzer --config cases/my_case/config.json
```

---

## Supported Data Sources

| Source | Format | Direction |
|--------|--------|-----------|
| SMS Backup & Restore | XML | Both (sent & received) |
| Phone Call Log | XML | Both directions |
| Signal Desktop | JSON (via extractor) | Both sides |
| Signal MSL Backup | JSON (protobuf extract) | Sent only |
| Manual Messages | JSON | Both (user-entered) |
| CSV Import | CSV (datetime, direction, body) | Both |

### CSV Format

```csv
datetime,direction,body
2025-01-15 14:30:00,sent,Hello how are you?
2025-01-15 14:32:00,received,I'm fine thanks
```

---

## Active Scripts (in active/ folder)

- **signal_desktop_extractor.py** — Extract messages from Signal Desktop's encrypted database
- **extract_signal_messages.py** — Extract Signal messages from MSL protobuf backup
- **generate_monthly_reports.py** — Generate per-month & weekly detailed analysis reports
- **parse_manual_messages.py** — Parse hand-typed message text files into JSON

All scripts accept `--config` for case-specific configuration. Run with `--help` for details.

---

## Tools (in tools/ folder)

Diagnostic and data-extraction utilities for working with source data.

- **explore_sms.py** — Inspect SMS backup XML database tables
- **debug_xml.py** — Debug and inspect XML data files
- **explore_signal.py** / **explore_db.py** — Browse Signal Desktop SQLCipher databases
- **extract_signal_desktop.py** / **read_signal_desktop.py** — Read Signal Desktop messages
- **extract_desktop_messages.py** — Extract messages from desktop export
- **decrypt_signal_key.py** — Decrypt Signal Desktop encryption key
- **deep_signal_check.py** / **deep_signal_check2.py** — Deep inspection of Signal data
- **redact_number.py** — Redact phone numbers from output files

All tools accept command-line arguments. Run with `--help` for usage.

---

## Installation

```bash
pip install -r requirements.txt
```

Required: `defusedxml`. Optional: `pycryptodome` (for Signal Desktop decryption).

---

## How Pattern Detection Works

The engine uses **context-aware regex matching** with validation functions and context filters to reduce false positives:

1. **Hurtful Language**: Only flags words directed AT a person (e.g., "fuck you" is flagged; "that movie was fucking great" is not)
2. **DARVO**: Requires manipulative context, not casual conversation
3. **Gottman's Horsemen**: Distinguishes character attacks from behavior feedback
4. **Coercive Control**: Flags controlling language about the other person's autonomy
5. **Context Filters**: Apologies, self-directed negativity, third-party venting, jokes, banter, de-escalation, and hurt expression are recognized and suppress false positives

Each detected pattern includes:
- Pattern category and clinical source
- Matched text snippet
- Full message for context
- Severity rating (1-10)

---

## References

1. Freyd, J.J. (1997). *Violations of power, adaptive blindness, and betrayal trauma theory.* Feminism & Psychology.
2. Gottman, J.M. & Silver, N. (1999). *The Seven Principles for Making Marriage Work.* Harmony Books.
3. Stark, E. (2007). *Coercive Control.* Oxford University Press.
4. Stern, R. (2007). *The Gaslight Effect.* Harmony Books.
5. Bancroft, L. (2002). *Why Does He Do That?* Berkley Books.
6. Arabi, S. (2017). *Becoming the Narcissist's Nightmare.* SCW Archer Publishing.
7. Forward, S. & Frazier, D. (1997). *Emotional Blackmail.* Harper Collins.
8. APA (2013). *DSM-5.* American Psychiatric Association.
9. Domestic Abuse Intervention Programs (1981). *Duluth Model Power and Control Wheel.*
10. Bateson, G. (1956). *Toward a Theory of Schizophrenia.* Behavioral Science.

---

## License

For personal and educational use. Not a substitute for professional legal or clinical advice. Pattern detection is probabilistic — always review flagged content in context.
