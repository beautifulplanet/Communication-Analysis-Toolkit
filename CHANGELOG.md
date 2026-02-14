# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-02-14
### Added
- **SQLite Engine:** Migrated from `DATA.json` to `cases.db` for 100k+ message scalability.
- **Dashboard:** New React/TypeScript visualization interface.
- **Safety:** Added `cases/README.md` warning about PII.
- **Privacy:** Added comprehensive `DATA_PRIVACY.md` policy.
- **Documentation:** Added `AUTHORS.md` and `CONTRIBUTING.md`.

### Changed
- **Rebranding:** Renamed "clinical-grade" to "research-informed" throughout the codebase.
- **Authorship:** Standardized project metadata to "Communication Analysis Team".
- **Performance:** Enabled WAL mode for SQLite to support concurrent writes.

### Fixed
- **CI/CD:** Fixed GitHub Actions pipeline failures.
- **Types:** Added strict `mypy` type checking across the engine.
- **Linting:** Enforced `ruff` rules for code quality.

## [3.0.0] - 2026-02-01
### Added
- Initial public release of the Pattern Matching Engine.
- Support for SMS XML, Signal Backup, and CSV ingestion.
