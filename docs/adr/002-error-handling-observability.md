# ADR 002: Error Handling & Observability Strategy

## Context
As the Communication Analysis Toolkit evolved from a research script to a production-grade API, debugging became increasingly difficult. Silent failures in the data ingestion pipeline and unhandled exceptions in the analysis agent led to a fragile user experience. We needed a robust strategy to handle errors gracefully and provide clear visibility into system behavior.

## Decision
We adopted a **"Resilience-First"** error handling strategy combined with **structured logging** for full observability.

### Error Handling Philosophy

1.  **Graceful Degradation:**
    *   **Layer 1 (Structured Engine):** If a regex fails or a key is missing in `DATA.json`, the engine catches the exception, logs a warning, and returns `None`. This automatically triggers a fallback to Layer 2 (RAG), ensuring the user still gets an answer.
    *   **Layer 2 (RAG):** If the retrieval fails or the LLM is unreachable, the agent returns a valid `AgentAnswer` object with `answer="I encountered an error..."` rather than raising an HTTP 500. This keeps the frontend operational.

2.  **Custom Exception Hierarchy:**
    *   Base class: `CommunicationForensicError`
    *   Specifics: `DataLoadingError`, `AnalysisError`, `AgentRetrievalError`.
    *   **Outcome:** Allows precise catch blocks and meaningful error messages to the user.

### Observability (Structlog)

We replaced standard `logging` with `structlog` to enforce JSON-structured logs.

*   **Why?**
    *   Machine-readable: Logs can be ingested by Splunk/Datadog/ELK without parsing rules.
    *   Contextual: We bind context variables (e.g., `request_id`, `user_id`) at the start of a request. Every subsequent log line automatically includes these fields.
    *   Sample Log:
        ```json
        {"event": "search_query", "query": "patterns in june", "layer": 2, "request_id": "123-abc", "level": "info", "timestamp": "..."}
        ```

### Request Tracing

*   **Mechanism:** Middleware generates a UUID `X-Request-ID` for every incoming HTTP request.
*   **Propagation:** This ID is passed to the `AnalysisAgent` and `RAGEngine`, binding it to all logs generated during that request's lifecycle.
*   **Benefit:** Allows tracing a single user interaction across multiple components (API -> Agent -> Retriever -> LLM).

## Consequences

### Positive
*   Ryle: The system is robust; one malformed message in a 50,000-message export is skipped with a warning, not a crash.
*   Debuggability: "What happened with request X?" can be answered instantly by filtering logs for that UUID.

### Negative
*   Verbosity: Logs are more voluminous.
*   Learning Curve: Developers must use `log.info("event_name", key=value)` instead of f-strings.

## Status
Accepted and Implemented (Sprint 3).
