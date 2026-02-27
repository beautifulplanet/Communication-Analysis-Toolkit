# ADR 003: SQLite Data Layer Schema

## Context
Currently, the tool loads all communication data into a single `DATA.json` file. For 3+ years of data (100k+ messages), this causes:
1.  **High Memory Usage:** The entire dataset must be loaded into RAM.
2.  **Slow Startup:** Parsing generic JSON is slow.
3.  **Analysis Latency:** Re-analyzing data requires rewriting the entire file.

## Decision
We will migrate to **SQLite** as the storage engine. This allows for:
-   Zero-latency selective loading (e.g., "just June 2025").
-   Efficient distinct lookups for the Agent.
-   Separation of **Raw Evidence** vs. **Analysis Interpretation**.

## Schema Design

### 1. `cases` Table
Stores metadata about the analysis case.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `name` | TEXT | Case name (e.g., "Export 2026") |
| `user_name` | TEXT | Name of the device owner |
| `contact_name` | TEXT | Name of the other party |
| `created_at` | TEXT | ISO8601 creation time |

### 2. `messages` Table (Raw Evidence)
Stores the immutable source data. This table is **Append-Only** during ingestion.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment ID |
| `case_id` | INTEGER | FK to `cases.id` |
| `timestamp` | INTEGER | Unix timestamp (sorting) |
| `date` | TEXT | "YYYY-MM-DD" (partitioning) |
| `time` | TEXT | "HH:MM" (display) |
| `source` | TEXT | "sms", "whatsapp", "signal" |
| `direction` | TEXT | "user->contact" or "contact->user" |
| `body` | TEXT | The actual message content |
| `media_type` | TEXT | "text", "image", "audio" |

**Indexes:**
-   `idx_messages_case_date` (`case_id`, `date`)
-   `idx_messages_timestamp` (`timestamp`)

### 3. `message_analysis` Table (Derived Data)
Stores the results of the pattern matching engine. This table can be **Truncated and Re-populated** when analysis logic changes, without touching raw messages.

| Column | Type | Description |
|---|---|---|
| `message_id` | INTEGER PK | FK to `messages.id` |
| `is_hurtful` | BOOLEAN | |
| `severity` | TEXT | "mild", "moderate", "severe" |
| `is_apology` | BOOLEAN | |
| `sentiment_score`| REAL | -1.0 to 1.0 (Future proofing) |
| `patterns_json` | TEXT | JSON list: `["gaslighting", "darvo"]` |
| `keywords_json` | TEXT | JSON list of matched keywords |

### 4. `daily_summaries` Table (Cache)
Stores aggregate stats for the Timeline view.

| Column | Type | Description |
|---|---|---|
| `case_id` | INTEGER | FK to `cases.id` |
| `date` | TEXT | "YYYY-MM-DD" |
| `msg_count` | INTEGER | Total messages |
| `avg_sentiment` | REAL | Average sentiment |
| `patterns_count`| INTEGER | Count of patterns detected |

## Implementation Strategy
1.  Create `engine/db.py` to handle connection/migrations.
2.  Create `engine/storage.py` to abstract data access.
3.  Update `engine/ingestion.py` to write to SQLite.
4.  Update `api/dependencies.py` to read from SQLite.
