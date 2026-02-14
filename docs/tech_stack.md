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
    *   **LLM Integration**: Constructs context-rich prompts for external LLMs (OpenAI, Anthropic) to answer user questions like "Was he gaslighting me?".

---

## Supported Data Sources

| Source | Format | Direction | Notes |
| :--- | :--- | :--- | :--- |
| **SMS Backup & Restore** | XML | Both | Standard Android backup format |
| **Call Logs** | XML | Both | Standard Android call log format |
| **Signal Desktop** | SQLite | Both | Decrypted via `sqlcipher` |
| **CSV** | CSV | Both | Custom import (Date, Direction, Body) |
| **Manual JSON** | JSON | Both | For transcribing handwritten notes/images |

---

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

---

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
