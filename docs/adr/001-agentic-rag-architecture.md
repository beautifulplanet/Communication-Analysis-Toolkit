# ADR 001: Agentic RAG Architecture

## Context
The Communication Analysis Toolkit requires an AI agent capable of answering user questions about relationship dynamics. Users ask a wide variety of questions, ranging from simple factual queries ("How many messages did we send?") to complex psychological inquiries ("Is there evidence of gaslighting?").

Using a Large Language Model (LLM) for every query is inefficient, slow, and potentially inaccurate for finding exact statistics in a large dataset. Conversely, hard-coded logic cannot handle the nuance of natural language questions about emotional patterns.

## Decision
We implemented a **multi-layered "Agentic RAG" architecture** that routes queries to the most appropriate and cost-effective resolution path.

### The Three Layers

1.  **Layer 1: Structured Query Engine (Deterministic)**
    *   **Purpose:** Handles factual questions about volume, dates, and countable patterns.
    *   **Mechanism:** Regex-based intent classification maps natural language to SQL-like aggregation functions over the pre-computed `DATA.json`.
    *   **Pros:** Instant response (<10ms), 100% accurate stats, zero LLM cost.
    *   **Triggers:** "how many", "who sent more", "worst day", "total messages".

2.  **Layer 2: RAG (Retrieval-Augmented Generation)**
    *   **Purpose:** Handles questions requiring context, examples, or synthesis of text.
    *   **Mechanism:**
        1.  **Retriever:** Filters messages by date, participant, and pre-computed behavioral labels (e.g., `patterns=['gaslighting']`).
        2.  **Context Construction:** Formats the filtered messages into a condensed prompt.
        3.  **LLM Call:** Sends the prompt to a lightweight model (e.g., Gemini Flash, GPT-4o-mini).
    *   **Pros:** Context-aware, capable of nuance, grounded in actual data.
    *   **Triggers:** "Show me examples of...", "What did they say about...", "Find messages where...".

3.  **Layer 3: Deep Analysis (Future/Optional)**
    *   **Purpose:** Comprehensive psychological profiling and multi-day trend analysis.
    *   **Mechanism:** Full context window processing or chain-of-thought reasonins with a reasoning model (e.g., o1, Gemini Pro).
    *   **Status:** Reserved for future implementation.

## Consequences

### Positive
*   **Cost Efficiency:** >60% of user queries (stats) are free.
*   **Accuracy:** Statistical answers are never "hallucinated" because they bypass the LLM.
*   **Speed:** The UI feels snappy for basic interactions.

### Negative
*   **Complexity:** Requires maintaining two separate engines (Structured & RAG) and a routing logic.
*   **Maintenance:** New query types must be manually added to the Layer 1 regex patterns, or they default to Layer 2 (which might fail to calculate exact stats accurately).

## Status
Accepted and Implemented (Sprint 3-8).
