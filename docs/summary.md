# Part 1: Project Summary

*Back to [main README](../README.md)*

---

## What

A local-first NLP engine that analyzes text-based communication (SMS, Signal, etc.) for behavioral patterns. It combines:

- **Regex-based pattern detection** grounded in peer-reviewed behavioral science (30+ negative patterns, 10+ positive patterns)
- **Context-aware filtering** that suppresses false positives (apologies, self-directed negativity, de-escalation, banter)
- **Bidirectional analysis** — both parties analyzed equally with the same rules
- **Three-layer AI agent** for natural-language questions about the data (Structured SQL → Keyword Retrieval → LLM Deep Analysis)
- **Full-stack local app** — Python engine, FastAPI REST API, React/TypeScript dashboard, SQLite persistence
- **Privacy-first architecture** — zero outbound network calls unless the user explicitly configures an LLM API key

### Key Outputs

| File | What it contains |
|---|---|
| `TIMELINE.md` | Day-by-day narrative flagging specific incidents with timestamps |
| `ANALYSIS.md` | Statistics: message volume, response patterns, behavioral breakdown by category |
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

## Why It's Interesting (for Interviewers)

| Talking Point | Detail |
|---|---|
| NLP / text analysis | Regex-based behavioral pattern detection with 30+ rules, context-aware false-positive filtering, peer-reviewed academic citations |
| Data engineering | Multi-format parser pipeline (XML, SQLite, CSV, JSON), SQLite WAL persistence, structured data pipeline |
| API design | FastAPI with Pydantic schemas, rate limiting, auth middleware, structured error handling, Celery async task queue |
| AI agent architecture | Three-layer Agentic RAG — most questions answered without any LLM call; 225 test questions validate routing |
| Testing discipline | 726 tests across 33 files covering pattern detection, API, agent, fuzz, golden snapshots, malformed data resilience |
| Security awareness | defusedxml (XXE prevention), path traversal checks, Fernet encryption-at-rest, request tracing, rate limiting |
| Full-stack ownership | Python engine + FastAPI API + React/TS dashboard + SQLite + Docker + structured logging — all one person |

---

## Key Numbers

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

---

## Context-Aware Filtering

To reduce false positives, negative flags are suppressed when the engine detects:
- **Apologies** ("I'm sorry", "My bad")
- **Self-Directed Negativity** ("I hate myself" vs. "I hate you")
- **De-escalation** ("Let's take a break", "I don't want to fight")
- **Banter/Jokes** (laughter, emojis, reciprocal tone)

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

*Continue to [Part 2: Technical Stack](tech_stack.md) or back to [main README](../README.md)*
