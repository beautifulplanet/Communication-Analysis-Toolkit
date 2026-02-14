# Communication Analysis Toolkit

[![CI](https://github.com/beautifulplanet/Communication-Analysis-Toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/beautifulplanet/Communication-Analysis-Toolkit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Version 3.1.0** — A research-informed forensic engine for analyzing text-based communication.

> **Privacy First:** This tool runs **100% locally**. Your data never leaves your machine.

---

## Documentation Parts

This README is divided into 4 parts for different audiences:

1.  **[Summary (Part 1)](docs/summary.md)**: High-level overview of features and pattern detection categories.
2.  **[Technical Stack (Part 2)](docs/tech_stack.md)**: Architecture, data sources, and development guide for engineers.
3.  **[Quick Start (Part 3)](docs/quick_start.md)**: Installation and usage instructions for developers.
4.  **[Tutorial (Part 4)](docs/tutorial.md)**: Step-by-step guide for non-technical users.

---

# Part 1: Summary

## What It Does

The **Communication Analysis Toolkit** is a research-informed forensic engine designed to analyze text-based communication (SMS, Signal, etc.) for behavioral patterns. It provides objective, data-driven insights into relationship dynamics, specifically detecting clinical patterns associated with high-conflict or manipulative interactions.

### Key Outputs
*   **TIMELINE.md**: A day-by-day narrative of the relationship, flagging specific incidents.
*   **ANALYSIS.md**: Comprehensive statistics including message volume, response times, and pattern breakdowns.
*   **EVIDENCE.md**: A catalog of every flagged message with its severity rating and clinical classification.
*   **DATA.json**: A machine-readable dataset of the entire analysis.

## Pattern Detection Categories

The engine uses regex-based detection grounded in peer-reviewed behavioral science.

### 🚩 Core Manipulation (DARVO)
*   **Deny**: Denying events that occurred.
*   **Attack**: Attacking the accuser to deflect blame.
*   **Reverse Victim & Offender**: Claiming victimhood when being the aggressor.
*(Source: Freyd, 1997)*

### 🚩 The "Four Horsemen"
*   **Criticism**: Attacking character rather than behavior.
*   **Contempt**: Expressions of superiority, mockery, or disgust.
*   **Defensiveness**: Counter-blaming or playing the victim.
*   **Stonewalling**: Withdrawal and refusal to engage.
*(Source: Gottman & Silver, 1999)*

### 🚩 Coercive Control
*   **Isolation**: Controlling who the person sees or talks to.
*   **Financial Control**: Using money as leverage.
*   **Weaponizing Health**: Using illness or trauma to manipulate.
*(Source: Stark, 2007)*

### 💛 Positive Communication (New in v3.1)
*   **Validation**: Acknowledging the other person's reality.
*   **Empathy**: Expressing understanding of feelings.
*   **Appreciation**: Expressing gratitude or value.
*   **Responsibility**: Owning one's own actions.

## Context-Aware Filtering
To reduce false positives, the system understands context. It suppression negative flags when it detects:
*   ✅ **Apologies** ("I'm sorry", "My bad")
*   ✅ **Self-Directed Negativity** ("I hate myself", not "I hate you")
*   ✅ **De-escalation** ("Let's take a break", "I don't want to fight")
*   ✅ **Banter/Jokes** (Detected via laughter, emojis, and reciprocal tone)

---

# Part 2: Technical Stack

## Architecture

The system is built on a modular "Agentic RAG" architecture designed for local-first privacy and scalability.

### Layers
1.  **Ingestion & Analysis Engine** (`engine/`):
    *   **Parsers**: XML (SMS/Calls), SQLite (Signal), JSON/CSV.
    *   **Analyzer**: Regex-based pattern detection with context-aware filtering.
    *   **Storage**: SQLite database for persistence of cases, messages, and analysis results.

2.  **API Layer** (`api/`):
    *   **FastAPI**: Provides REST endpoints for the frontend and agent.
    *   **Async Processing**: Celery + Redis for handling large dataset ingestion in the background.

3.  **Agentic AI** (`api/agent.py`):
    *   **RAG Engine**: Retrieves relevant messages based on semantic query analysis.
    *   **LLM Integration**: Constructs context-rich prompts for external LLMs (OpenAI, Anthropic) to answer user questions.

## Supported Data Sources

| Source | Format | Direction | Notes |
| :--- | :--- | :--- | :--- |
| **SMS Backup & Restore** | XML | Both | Standard Android backup format |
| **Call Logs** | XML | Both | Standard Android call log format |
| **Signal Desktop** | SQLite | Both | Decrypted via `sqlcipher` |
| **CSV** | CSV | Both | Custom import (Date, Direction, Body) |
| **Manual JSON** | JSON | Both | For transcribing handwritten notes/images |

## Active Scripts

Located in `active/`:
*   `signal_desktop_extractor.py`: Decrypts and extracts messages from Signal Desktop's local database.
*   `generate_monthly_reports.py`: Aggregates daily analysis into monthly summaries.

## Diagnostic Tools

Located in `tools/`:
*   `names.py`: Anonymize names in the dataset.
*   `redact_number.py`: scrub phone numbers from output files.
*   `explore_db.py`: Inspect the SQLite database structure.
*   `debug_xml.py`: Validate XML structure before ingestion.

## Development

### Prerequisites
*   Python 3.11+
*   Redis (for async tasks)
*   Docker (optional, for full stack execution)

### Testing
We use `pytest` for unit and integration testing.
```bash
pytest
```

### Type Checking & Linting
We enforce strict typing and code style.
```bash
mypy .
ruff check .
```

---

# Part 3: Quick Start Guide

## Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/beautifulplanet/Communication-Analysis-Toolkit.git
    cd Communication-Analysis-Toolkit
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## Running Your First Analysis

### 1. Prepare Your Data
Place your `sms_backup.xml` (from SMS Backup & Restore) or `calls.xml` into a new folder:
`cases/my_case/source_data/`

### 2. Configure the Analysis
Create `cases/my_case/config.json`:

```json
{
    "case_name": "My Case",
    "user_label": "Me",
    "contact_label": "Ex-Partner",
    "sms_xml": "./cases/my_case/source_data/sms_backup.xml",
    "output_dir": "./cases/my_case/output",
    "date_start": "2020-01-01",
    "date_end": "2025-12-31"
}
```

### 3. Run the Engine
```bash
python -m engine.analyzer --config cases/my_case/config.json
```

## Viewing Results

Navigate to `cases/my_case/output/` to inspect:

*   **`ANALYSIS.md`**: High-level statistical overview.
*   **`TIMELINE.md`**: Chronological narrative of flagged events.
*   **`EVIDENCE.md`**: Detailed list of every flagged message.

### Advanced Usage: AI Assistant
To ask questions like *"When did he start gaslighting me?"*:

1.  Start the API server:
    ```bash
    uvicorn api.main:app --reload
    ```
2.  Open your browser to `http://localhost:8000/docs`.
3.  Use the `/agent/chat` endpoint to query your case data.

---

# Part 4: Tutorial for Non-Technical Users

Welcome! This guide is for anyone who wants to analyze their own communication data without needing to know how to code.

**Prerequisites**: You will need a computer (Windows/Mac/Linux) and basic familiarity with using the terminal/command prompt.

## Step 1: Get Your Data

To analyze your messages, you first need to export them from your phone.

### For Android Users (SMS/MMS)
1.  Download **SMS Backup & Restore** from the Play Store.
2.  Open the app and tap **Backup**.
3.  Select "Text Messages" (and "Call Logs" if desired).
4.  Choose "Local Backup" and save the XML file to your phone.
5.  Transfer this file (`sms_backup.xml`) to your computer.

### For Signal Users
1.  See our [Signal Extraction Guide](docs/signal_extraction.md) (coming soon) or use the `signal_desktop_extractor.py` script if you have Signal Desktop installed.

## Step 2: Install the Toolkit

1.  Download and install **Python** from [python.org](https://www.python.org/downloads/). (Make sure to check "Add Python to PATH" during installation).
2.  Download this toolkit as a ZIP file from GitHub (click the green "Code" button -> "Download ZIP") and extract it.
3.  Open your terminal (Command Prompt on Windows, Terminal on Mac).
4.  Navigate to the extracted folder:
    ```bash
    cd Downloads/Communication-Analysis-Toolkit
    ```
5.  Install the required software:
    ```bash
    pip install -r requirements.txt
    ```

## Step 3: Set Up Your Case

Think of a "case" as a folder for one specific relationship or investigation.

1.  Create a folder named `my_case` inside the `cases/` folder.
2.  Inside `my_case`, create a folder named `source_data`.
3.  Copy your `sms_backup.xml` file into `cases/my_case/source_data/`.
4.  Create a simple text file named `config.json` inside `cases/my_case/` with this content:
    *(You can use Notepad or TextEdit)*

    ```json
    {
        "case_name": "My Relationship Analysis",
        "user_label": "Me",
        "contact_label": "Them",
        "sms_xml": "./cases/my_case/source_data/sms_backup.xml",
        "output_dir": "./cases/my_case/output",
        "date_start": "2020-01-01",
        "date_end": "2025-12-31"
    }
    ```

## Step 4: Run the Analysis

In your terminal, run this command:

```bash
python -m engine.analyzer --config cases/my_case/config.json
```

It will process your messages and tell you when it's done.

## Step 5: Read Your Reports

Go to the `cases/my_case/output/` folder. You will find several files:

*   **`TIMELINE.md`**: A story-like view of your relationship day-by-day. Open this in any Markdown viewer or text editor. It highlights arguments, pattern escalations, and mood shifts.
*   **`ANALYSIS.md`**: The numbers. How many messages? Who engaged more? What patterns appeared most often?
*   **`EVIDENCE.md`**: The specific texts. Every time the system flagged a high-conflict pattern (like gaslighting or severe insults), it's listed here with the date and message content.

Questions? Check the [Summary (Part 1)](docs/summary.md) to understand what the patterns mean.

---

## License

For personal and educational use. Not a substitute for professional legal or clinical advice. Pattern detection is probabilistic — always review flagged content in context.
