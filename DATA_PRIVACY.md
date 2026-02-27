# Data Privacy & Security Policy

**Last Updated:** 2026-02-13

## 1. Local-First Architecture
The Communication Analysis Toolkit is designed as **Local-First Software**.
-   **No Data Uploads:** All analysis happens on your local machine (`localhost`).
-   **No Telemetry:** We do not track usage, collect metrics, or send crash reports to external servers.
-   **No Cloud Sync:** Your case data lives in the `cases/` directory and nowhere else.

## 2. PII Handling (Personally Identifiable Information)
The tool processes sensitive personal communications.
-   **Storage:** Raw messages are stored in `DATA.json` or SQLite databases within the `cases/` directory.
-   **Exclusion:** The `cases/` directory is explicitly excluded from version control via `.gitignore` to prevent accidental leaks.
-   **Risk:** Users are responsible for securing their own `cases/` folder (e.g., via disk encryption like BitLocker or FileVault).

## 3. AI & Third-Party Services
-   **Local Analysis:** The core analysis engines (Pattern Matching, Keyword Search) do not use external APIs.
-   **AI Audits (Optional):** If you choose to use the "AI Prompt" feature to send data to third-party LLMs (ChatGPT, Claude, etc.), you are subject to *their* privacy policies. We strip names/emails from generated prompts where possible, but you must review all data before submission.

## 4. Compliance
This software is provided for self-hosted communication analysis. It is not HIPAA or GDPR compliant by default, as it is a developer tool, not a managed service.
