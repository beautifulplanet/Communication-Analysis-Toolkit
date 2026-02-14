# Contributing to Communication Analysis Toolkit

Thank you for your interest in contributing to the **Communication Analysis Toolkit**!
We welcome contributions from researchers, developers, and data scientists.

## 🤝 Code of Conduct

This project is intended for **ethical research purposes**.
*   **Do not** add features that enable non-consensual surveillance ("stalkerware").
*   **Do not** weaken the privacy guarantees (local-only processing).

## 🛠️ Development Setup

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/beautifulplanet/Communication-Analysis-Toolkit.git
    cd Communication-Analysis-Toolkit
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run Tests:**
    ```bash
    pytest
    ```

## 🧪 Testing Guidelines

*   We use `pytest` for unit and integration testing.
*   New features must include tests.
*   **Do not commit real PII.** Use the mock data generators in `tests/`.

## 📝 Style Guide

We use strict linting to maintain code quality:

```bash
# Run linter
ruff check .

# Run type checker
mypy .
```

## 🚀 Pull Request Process

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes.
4.  Run tests and linters.
5.  Open a Pull Request.

Thank you for helping us make communication analysis more accessible and rigorous!
