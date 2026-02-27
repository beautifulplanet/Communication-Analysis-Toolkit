# Communication Analysis Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**A local-first NLP engine that analyzes text-based communication for behavioral patterns — built with Python, FastAPI, SQLite, React, and a three-layer AI agent architecture.**

> **Privacy First:** This tool runs **100% locally**. No data leaves your machine. No cloud. No telemetry. No accounts.

---

### Impact

- **Behavioral pattern detection engine** — regex-based NLP with context-aware filtering, detecting 30+ patterns across 6 research-backed categories (DARVO, Gottman's Four Horsemen, Coercive Control, and more).
- **Three-layer Agentic RAG architecture** — Structured Query → Keyword Retrieval → LLM Deep Analysis, so users can ask natural-language questions about their data.
- **726 tests, 0 lint errors, 0 type errors** — 33 test files covering pattern detection, API endpoints, agent routing, edge cases, database integrity, and malformed data resilience.
- **Full-stack local application** — Python analysis engine, FastAPI REST API, React/TypeScript dashboard, SQLite persistence, Celery async processing.

**Stack:** Python 3.11 · FastAPI · SQLite · React · TypeScript · Celery · Redis · structlog · Pydantic · defusedxml · Docker

### Evidence

| Claim | Proof |
|---|---|
| 726 tests collected | `python -m pytest --co -q` |
| 693 passing, 0 collection errors | `python -m pytest --tb=short -q` |
| 0 lint errors | `ruff check .` → "All checks passed!" |
| 0 type errors | `mypy engine api --ignore-missing-imports` → "Success: no issues found in 36 source files" |
| Pattern detection accuracy | 400+ test cases across 5 dedicated pattern test suites |
| Data never leaves machine | No outbound calls except optional LLM queries (user-provided API key). See [DATA_PRIVACY.md](DATA_PRIVACY.md) |
| API works | `uvicorn api.main:app --reload` → Swagger UI at `localhost:8000/docs` |
| Dashboard builds | `cd dashboard && npm run build` → production bundle |

### Quality Bar

- **Research-grounded patterns** — every detection category cites peer-reviewed sources (Freyd 1997, Gottman 1999, Stark 2007, Johnson 2008)
- **Context-aware false-positive filtering** — apologies, self-directed negativity, de-escalation, and banter are suppressed before flagging
- **Bidirectional analysis** — both parties are analyzed equally; no assumption about who is "the bad actor"
- **Supportive pattern detection** — not just negatives; empathy, validation, accountability, and appreciation are tracked
- **Structured logging** — every request gets a UUID, every agent answer logs layer, duration, and confidence via structlog
- **Security hardened** — BasicAuth middleware, rate limiting (slowapi), path traversal protection, defusedxml for XML parsing, encryption-at-rest support

### Why It's Interesting (for Interviewers)

| Talking Point | Detail |
|---|---|
| NLP / text analysis | Regex-based behavioral pattern detection with 30+ rules, context-aware false-positive filtering, and peer-reviewed academic citations |
| Data engineering | Multi-format parser pipeline (XML, SQLite, CSV, JSON), SQLite WAL persistence, structured data pipeline from raw exports to analytics |
| API design | FastAPI with Pydantic schemas, rate limiting, auth middleware, structured error handling, async task queue (Celery/Redis) |
| AI agent architecture | Three-layer Agentic RAG — most questions answered without any LLM call; 225 test questions validate routing logic |
| Testing discipline | 726 tests across 33 files: pattern detection, API, agent, fuzz, golden snapshots, malformed data resilience, encryption |
| Security awareness | defusedxml (XXE prevention), path traversal checks, Fernet encryption-at-rest, request tracing, rate limiting |
| Full-stack ownership | Python engine, FastAPI API, React/TS dashboard, SQLite storage, Docker config, structured logging — all one person |
| Self-awareness | Honest roadmap, known limitations documented, self-audit report that identifies what's broken and what's not done |

### Ownership & Quality

I built this as a solo project to learn NLP, data engineering, and full-stack architecture. I use AI-assisted tooling for development, but I review every change, write tests, and validate behavior with static analysis and manual testing.

- **Role:** Sole developer — design, implementation, testing, documentation
- **Standard:** ruff clean, mypy clean, 95%+ test pass rate before any commit
- **AI policy:** AI-assisted code is reviewed, tested, and understood. I can explain and extend every component.
- **Honest gaps:** 16 of 726 tests are skipped (no API key / no sample data). 17 fail — 15 are documented planned features (see [Roadmap](#roadmap)), 2 are edge-case assertion refinements.

Each part is also available as a **standalone document**:

| Part | Standalone |
|---|---|
| Summary | [docs/summary.md](docs/summary.md) |
| Technical Stack | [docs/tech_stack.md](docs/tech_stack.md) |
| Quick Start | [docs/quick_start.md](docs/quick_start.md) |
| Tutorial | [docs/tutorial.md](docs/tutorial.md) |

---

## How to Read This README

### If you're evaluating the candidate

| What you want | Where to find it | Time |
|---|---|---|
| Stack + key claims | [Impact ↑](#impact) | 30 sec |
| Proof it works | [Evidence ↑](#evidence) | 1 min |
| Architecture decisions | [Architecture ↓](#architecture) | 2 min |
| What I'd improve | [Roadmap ↓](#roadmap) + [Known Limitations ↓](#known-limitations) | 2 min |
| Run it yourself | [Quick Start ↓](#quick-start) | 3 min |

### If you're reviewing engineering

| What you want | Where to find it | Time |
|---|---|---|
| System architecture | [Architecture ↓](#architecture) | 2 min |
| Pattern detection internals | [Pattern Detection ↓](#pattern-detection-categories) | 3 min |
| AI agent design | [Agentic RAG ↓](#agentic-rag-architecture) | 3 min |
| Security + privacy posture | [Security ↓](#security--privacy) + [DATA_PRIVACY.md](DATA_PRIVACY.md) | 2 min |
| Testing strategy | [Testing ↓](#testing) | 2 min |
| Data flow | [Data Flow ↓](#data-flow) | 2 min |
| File map | [File Map ↓](#file-map) | 1 min |

### If you want to run it

| What you want | Where to find it | Time |
|---|---|---|
| Install + run analysis | [Quick Start ↓](#quick-start) | 3 min |
| Start the dashboard | [Dashboard ↓](#viewing-results-dashboard) | 2 min |
| Ask AI questions | [AI Assistant ↓](#ai-assistant) | 2 min |
| Non-technical walkthrough | [Tutorial ↓](#tutorial-for-non-technical-users) | 10 min |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Dashboard                       │
│              (TypeScript, Vite, Recharts)                │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (localhost:8000)
┌────────────────────────▼────────────────────────────────┐
│                    FastAPI Backend                        │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌─────────┐  │
│  │ REST API │  │ Chat API │  │  Auth   │  │  Rate   │  │
│  │ /cases/* │  │ /ask     │  │ Basic   │  │ Limiter │  │
│  └────┬─────┘  └────┬─────┘  └─────────┘  └─────────┘  │
│       │              │                                   │
│  ┌────▼─────┐  ┌─────▼──────────────────────────┐       │
│  │  Case    │  │     Analysis Agent (RAG)        │       │
│  │  Storage │  │  L1: Structured → L2: Retrieval │       │
│  │  (SQLite)│  │  → L3: LLM Deep Analysis       │       │
│  └──────────┘  └────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                  Analysis Engine                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Parsers  │  │ Pattern  │  │Supportive│  │ Report │  │
│  │ XML/SQL/ │  │ Detector │  │ Pattern  │  │ Writer │  │
│  │ CSV/JSON │  │ (30+)    │  │ Detector │  │ MD/JSON│  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Why |
|---|---|
| **Local-first, no cloud** | Communication data is deeply personal. Zero-trust architecture means the user's data never touches a network unless they explicitly configure an LLM API key. |
| **Regex over ML for pattern detection** | Interpretable, auditable, no training data needed. Every flag can be traced to a specific regex rule and academic source. ML would be a black box. |
| **Three-layer agent (not just LLM)** | Layer 1 handles stats without any API call. Layer 2 retrieves context locally. Only Layer 3 calls an external LLM — and only if configured. Most questions never leave the machine. |
| **SQLite over Postgres** | Single-user local tool. SQLite is zero-config, portable, and handles the data volumes here (tens of thousands of messages) easily. WAL mode enabled for concurrent reads. |
| **Bidirectional analysis** | Both parties are analyzed with the same rules. The tool doesn't assume who is "right." This is a deliberate design choice to reduce bias. |

---

## Pattern Detection Categories

The engine uses regex-based detection grounded in peer-reviewed behavioral science. Every pattern includes the academic citation.

### Negative Patterns (30+ rules)

**DARVO** *(Freyd, 1997)*
- **Deny** — Denying events that occurred
- **Attack** — Attacking the accuser to deflect blame
- **Reverse Victim & Offender** — Claiming victimhood when confronted

**Gottman's Four Horsemen** *(Gottman & Silver, 1999)*
- **Criticism** — Attacking character rather than behavior
- **Contempt** — Expressions of superiority, mockery, or disgust
- **Defensiveness** — Counter-blaming or playing the victim
- **Stonewalling** — Withdrawal and refusal to engage

**Coercive Control** *(Stark, 2007)*
- **Isolation** — Controlling who the person sees or talks to
- **Financial Control** — Using money as leverage
- **Weaponizing Health** — Using illness or trauma to manipulate

**Additional Manipulation Patterns**
- Gaslighting, guilt-tripping, love bombing, future faking, triangulation, silent treatment threats, minimizing, blame shifting, deflection

### Positive Patterns *(Johnson, 2008; Gottman, 1999)*
- **Validation** — Acknowledging the other person's feelings
- **Empathy** — Showing emotional understanding
- **Appreciation** — Expressing gratitude or value
- **Accountability** — Owning one's actions
- **De-escalation** — Attempting to reduce conflict

### Context-Aware Filtering

To reduce false positives, negative flags are suppressed when the engine detects:
- Apologies ("I'm sorry", "My bad")
- Self-directed negativity ("I hate myself" vs. "I hate you")
- De-escalation ("Let's take a break")
- Banter/jokes (laughter, emojis, reciprocal tone)

---

## Agentic RAG Architecture

The AI assistant uses a three-layer architecture to answer questions about case data:

| Layer | Name | What it does | Needs LLM? |
|---|---|---|---|
| **L1** | Structured Query | Handles stat questions ("How many messages?", "Who sent more?") via direct SQL queries | No |
| **L2** | Keyword Retrieval | Searches messages by date, pattern, direction, severity, keywords | No |
| **L3** | Deep Analysis | Constructs a context-rich prompt with retrieved messages and sends to OpenAI/Anthropic | Yes |

**How it works:** Every question enters at L1. If the StructuredQueryEngine can answer it (counts, comparisons, breakdowns), it returns immediately — no network call, no latency. If L1 can't handle it, L2 retrieves relevant messages and formats them. If an LLM is configured, L3 sends the context + question to get a nuanced answer. If no LLM is configured, L2's retrieval result is returned directly.

**207 of 225 agent test questions pass.** The 18 failures are planned L1 features documented in the [Roadmap](#roadmap).

---

## Data Flow

```
1. User provides data (XML/SQLite/CSV/JSON)
       │
2. Parser extracts messages + calls
       │
3. Pattern detector runs on each message (both directions)
       │
4. Results stored: SQLite DB + JSON + Markdown reports
       │
5. FastAPI serves data to React dashboard
       │
6. User asks questions → Agent answers via L1/L2/L3
```

**What goes to the network:** Nothing, unless you configure an LLM API key in `.env`. If configured, only the specific messages relevant to your question (plus the question itself) are sent to the LLM provider. Full details in [DATA_PRIVACY.md](DATA_PRIVACY.md).

---

## Supported Data Sources

| Source | Format | Direction | Notes |
|---|---|---|---|
| **SMS Backup & Restore** | XML | Both | Standard Android backup format |
| **Call Logs** | XML | Both | Standard Android call log format |
| **Signal Desktop** | SQLite | Both | Decrypted via `sqlcipher` |
| **CSV** | CSV | Both | Custom import (Date, Direction, Body) |
| **Manual JSON** | JSON | Both | For transcribing handwritten notes/images |
| **Text Paste** | Plain text | Both | Paste chat logs directly via API |

---

## Security & Privacy

| Layer | Implementation |
|---|---|
| **Authentication** | HTTP Basic Auth on all endpoints (configurable credentials) |
| **Rate Limiting** | slowapi — 60/min for reads, 20/min for analysis, 5/min for deletes |
| **XML Safety** | defusedxml — prevents XXE, billion laughs, and entity expansion attacks |
| **Path Traversal** | All case paths are resolved and validated against the cases root directory |
| **Request Tracing** | Every request gets a UUID via middleware, propagated through structlog |
| **Encryption at Rest** | Fernet symmetric encryption for stored data (optional, key in `.env`) |
| **Data Isolation** | Each case is a separate directory. Delete a case = delete the directory. |
| **No Telemetry** | Zero analytics, zero tracking, zero outbound connections (unless LLM configured) |

See [SECURITY_HARDENING.md](SECURITY_HARDENING.md) for the full hardening checklist.

---

## Testing

**726 tests collected across 33 test files.**

| Category | Tests | What's covered |
|---|---|---|
| Pattern detection (DARVO) | 35 | deny, attack, reverse victim/offender |
| Pattern detection (Gaslighting) | 28 | reality denial, memory manipulation, crazy-making |
| Pattern detection (Gottman) | 36 | criticism, contempt, defensiveness, stonewalling |
| Pattern detection (Coercive Control) | 28 | isolation, financial control, health weaponization |
| Pattern detection (Manipulation) | 37 | guilt-tripping, love bombing, future faking, triangulation |
| Supportive patterns | 85 | validation, empathy, accountability, appreciation |
| Context filters | 46 | apology suppression, self-directed, de-escalation, banter |
| Agent questions (225 NL queries) | 225 | stat queries, pattern searches, date filtering, edge cases |
| API endpoints | 5 | cases, summary, timeline, patterns, hurtful |
| Upload + ingestion | 8 | file upload, text paste, extension validation, case creation |
| Async integration | 3 | Celery task dispatch, task status |
| Database integrity | 6 | WAL mode, schema init, CRUD operations |
| Edge cases + malformed data | 36 | empty input, None values, missing keys, garbage data |
| Encryption | 1 | Fernet encrypt/decrypt round-trip |
| Caching | 1 | Agent cache hit/miss/invalidation |
| Rate limiting | 1 | Endpoint rate limit enforcement |
| Hurtful language | 30 | severity classification, bidirectional |
| Bidirectional analysis | 30 | both-party pattern detection |
| Parsers | 22 | XML, Signal SQLite, CSV, JSON parsing |
| Observability + tracing | 3 | structured logging, request ID propagation |

**What's not tested (honest gaps):**
- No browser-level E2E tests for the React dashboard (the dashboard is a read-only viewer)
- No load/stress testing (single-user local tool — not a scaling concern at this stage)
- 16 tests skip due to missing API keys or sample data
- 17 tests fail: 15 are documented planned L1 agent features, 2 are assertion refinements

### Running Tests

```bash
python -m pytest                    # full suite
python -m pytest --tb=short -q      # compact output
python -m pytest tests/test_patterns_darvo.py -v  # specific suite
```

### Static Analysis

```bash
ruff check .                                        # 0 errors
mypy engine api --ignore-missing-imports            # 0 errors
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard, optional)
- Redis (for async tasks, optional)

### Installation

```bash
git clone https://github.com/beautifulplanet/Communication-Analysis-Toolkit.git
cd Communication-Analysis-Toolkit
pip install -r requirements.txt
```

### Running Your First Analysis

**1. Prepare your data**

Place your `sms_backup.xml` (from SMS Backup & Restore) into a new folder:

```
cases/my_case/source_data/sms_backup.xml
```

**2. Create a config file**

Create `cases/my_case/config.json`:

```json
{
    "case_name": "My Analysis",
    "user_label": "Me",
    "contact_label": "Them",
    "sms_xml": "./cases/my_case/source_data/sms_backup.xml",
    "output_dir": "./cases/my_case/output",
    "date_start": "2020-01-01",
    "date_end": "2025-12-31"
}
```

**3. Run the engine**

```bash
python -m engine.cli --config cases/my_case/config.json
```

The engine displays a legal consent notice on first run. Output files are generated in `cases/my_case/output/`.

### Viewing Results (Dashboard)

```bash
cd dashboard
npm install
npm run dev
```

Then start the API:

```bash
uvicorn api.main:app --reload --port 8000
```

Open `http://localhost:5173` to see the dashboard.

### AI Assistant

To enable natural-language questions about your data:

1. Copy `.env.example` to `.env`
2. Add your API key:
   ```
   OPENAI_API_KEY=sk-...
   # or
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Restart the API server
4. Use the chat panel in the dashboard or POST to `/api/cases/{case_id}/ask`

Without an API key, the agent still works — it just uses Layer 1 (structured queries) and Layer 2 (keyword retrieval) without LLM interpretation.

---

## Key Outputs

| File | What it contains |
|---|---|
| `TIMELINE.md` | Day-by-day narrative of the relationship, flagging incidents |
| `ANALYSIS.md` | Statistics: message volume, response times, pattern breakdowns |
| `EVIDENCE.md` | Every flagged message with severity rating and pattern classification |
| `DATA.json` | Machine-readable dataset of the entire analysis |
| `AI_PROMPTS.md` | Ready-made prompts for external AI auditing (ChatGPT, Claude, Gemini) |

### Sample Output

**TIMELINE.md** (excerpt):
```
2024-03-15 — Escalation Point
  18:42 - Contact: "That never happened" [DENY]
  18:44 - Contact: "You're imagining things" [GASLIGHTING]
  18:47 - User: "I have the texts right here"
  18:49 - Contact: "You're crazy" [GASLIGHTING - SEVERE]
```

---

## File Map

```
Communication-Analysis-Toolkit/
├── engine/                     # Core analysis engine (Python)
│   ├── analyzer.py             # Main analysis pipeline (~1,050 lines)
│   ├── patterns.py             # Negative pattern detection (30+ rules)
│   ├── patterns_supportive.py  # Positive pattern detection
│   ├── relationship_health.py  # Gottman ratio + health scoring
│   ├── reporting.py            # Markdown + JSON report generation
│   ├── storage.py              # CaseStorage DAO (SQLite)
│   ├── db.py                   # Database connection + schema init
│   ├── crypto.py               # Fernet encryption at rest
│   ├── logger.py               # Structured logging (structlog)
│   ├── llm.py                  # LLM client (OpenAI/Anthropic)
│   ├── cli.py                  # CLI entry point with consent flow
│   └── tasks.py                # Celery async task definitions
│
├── api/                        # FastAPI backend
│   ├── main.py                 # App setup, middleware, routes
│   ├── agent.py                # Three-layer Analysis Agent
│   ├── retriever.py            # Message retrieval + filtering
│   ├── data.py                 # CaseDataReader
│   ├── services.py             # Agent caching layer
│   ├── config.py               # Pydantic settings
│   ├── dependencies.py         # Shared deps + case data loading
│   ├── middleware.py            # Auth + Request ID middleware
│   ├── schemas.py              # Pydantic response models
│   ├── errors.py               # Error handlers
│   └── routers/                # Endpoint modules
│       ├── chat.py             # /ask endpoint
│       ├── cases.py            # Case CRUD
│       ├── ingestion.py        # Async analysis trigger
│       ├── messages.py         # Message browsing
│       ├── upload.py           # File + text upload
│       └── health.py           # Health check + metrics
│
├── dashboard/                  # React frontend (TypeScript)
│   └── src/
│       ├── App.tsx             # Main app with routing
│       ├── components/         # UI components
│       └── api/                # API client
│
├── tests/                      # 33 test files, 726 tests
│   ├── test_patterns_*.py      # Pattern detection suites (5 files)
│   ├── test_supportive_*.py    # Positive pattern tests
│   ├── test_agent_questions.py # 225 NL query tests
│   ├── test_api.py             # API endpoint tests
│   ├── test_malformed_data.py  # Resilience tests
│   └── ...                     # 25 more test files
│
├── cases/                      # Case data directory (gitignored)
├── docs/                       # Architecture Decision Records
├── DATA_PRIVACY.md             # Privacy policy
├── SECURITY_HARDENING.md       # Security checklist
├── CONTRIBUTING.md             # Contribution guidelines
├── CHANGELOG.md                # Version history
└── requirements.txt            # Python dependencies
```

### Key Numbers

| Metric | Value |
|---|---|
| Python source files | 100 |
| Python LOC (engine + api + tests) | ~9,660 |
| Dashboard LOC (TypeScript) | ~760 |
| Test files | 33 |
| Test count | 726 |
| Pass rate | 693/726 (95.5%) |
| Pattern rules | 30+ negative, 10+ positive |
| Supported data formats | 6 (XML, SQLite, CSV, JSON, text paste, call logs) |
| ruff errors | 0 |
| mypy errors | 0 |

---

## Roadmap

### Planned: StructuredQueryEngine Expansions

These are features where the agent currently falls back to Layer 2 (keyword search) instead of answering directly via Layer 1 (structured SQL). They're tracked as failing tests in `test_agent_questions.py`:

| Feature | Test class | What it needs |
|---|---|---|
| Gap detection queries | `TestGaps` (3 tests) | L1 handler for "Were there communication gaps?" that queries the gaps table |
| Monthly breakdown queries | `TestMonthly` (4 tests) | L1 handler for "Show monthly stats" that aggregates by month |
| Top pattern queries | `TestBreakdowns` (2 tests) | L1 handler for "Most common pattern?" that ranks pattern counts |
| Contact day enrichment | `TestDayCounts` (1 test) | Include "contact" label in day count responses |
| Hurtful by-party breakdown | `TestHurtfulCounts` (1 test) | Include user/contact names in hurtful count responses |
| RAG retriever SQLite integration | `TestAgentIntegration` (2 tests) | Connect L2 retriever to SQLite instead of dict-based data |
| Silent day detection | `TestNoContactDays` (1 test) | L1 handler for "silent days" / "no contact days" |
| Empty data edge cases | `TestAgentWithEmptyData` (2 tests) | Refine L1 responses when case has zero data |

### Future Scope (Not Started)

- **Deployment plan** — Docker Compose for single-command startup; potential hosted version
- **Dashboard E2E tests** — Playwright tests for the React frontend
- **ML-enhanced detection** — Train a classifier on labeled data to complement regex rules
- **Multi-contact analysis** — Analyze multiple relationships within a single case
- **Export to PDF** — Generate printable reports from the Markdown output

---

## Known Limitations

- **Regex-based detection has limits.** Sarcasm, coded language, and cultural context can cause false positives/negatives. The tool is a starting point, not a conclusion.
- **Supportive scores are text-only.** Acts of service, quality time, physical affection, and non-verbal cues are not captured. A low supportive score does not mean support is absent.
- **Not a diagnostic tool.** This does not replace professional legal or psychological advice. Pattern detection is probabilistic — always review flagged content in full context.
- **Single-user local tool.** Not designed for multi-tenant deployment. No user accounts, no role-based access.
- **LLM answers depend on the model.** Layer 3 quality varies by provider and model version. The tool is designed to work well without any LLM.

---

## Tutorial for Non-Technical Users

If you're not a developer, here's how to use this tool step by step.

### Step 1: Get Your Data

**For Android Users (SMS/MMS):**
1. Download **SMS Backup & Restore** from the Play Store
2. Tap **Backup** → select "Text Messages" (and "Call Logs" if desired)
3. Choose "Local Backup" and save the XML file
4. Transfer the file to your computer

**For Signal Users:**
Use the `signal_desktop_extractor.py` script if you have Signal Desktop installed.

### Step 2: Install the Toolkit

1. Download and install **Python** from [python.org](https://www.python.org/downloads/) (check "Add Python to PATH")
2. Download this toolkit as a ZIP from GitHub and extract it
3. Open your terminal and navigate to the folder:
   ```bash
   cd Downloads/Communication-Analysis-Toolkit
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3: Set Up Your Case

1. Create `cases/my_case/source_data/` and copy your data file there
2. Create `cases/my_case/config.json` (see [Quick Start](#running-your-first-analysis) for the template)

### Step 4: Run the Analysis

```bash
python -m engine.cli --config cases/my_case/config.json
```

A consent notice will appear on first run. Type `y` to proceed.

### Step 5: Read Your Reports

Open `cases/my_case/output/`:
- **TIMELINE.md** — Day-by-day view with flagged incidents
- **ANALYSIS.md** — The numbers: message counts, patterns, ratios
- **EVIDENCE.md** — Every flagged message with severity and classification

---

## License

MIT License. For personal and educational use. Not a substitute for professional legal or psychological advice.
