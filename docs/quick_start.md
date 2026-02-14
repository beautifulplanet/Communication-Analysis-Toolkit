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

---

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

---

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
