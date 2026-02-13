"""
================================================================================
Communication Analysis Toolkit — CLI Entry Point
================================================================================

Handles command-line arguments and user consent before launching the analysis.
"""

import argparse
import os
import sys
from datetime import datetime

from engine.analyzer import run_analysis
from engine.logger import logger, setup_logging

_CONSENT_TEXT = """
╔══════════════════════════════════════════════════════════════════════╗
║                     IMPORTANT LEGAL NOTICE                         ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  This tool analyzes personal communication data. Before running:   ║
║                                                                    ║
║  1. You must have LEGAL AUTHORITY to analyze this data.            ║
║     (Your own messages, or data you have legal access to.)         ║
║                                                                    ║
║  2. This tool does NOT produce legally admissible evidence.        ║
║     Output is probabilistic pattern detection, not forensic proof. ║
║                                                                    ║
║  3. Consult an attorney before relying on any analysis in legal    ║
║     proceedings (custody, divorce, restraining orders, etc.).      ║
║                                                                    ║
║  4. Pattern detection can produce false positives and false        ║
║     negatives. Always review flagged content in full context.      ║
║                                                                    ║
║  5. This is NOT a diagnostic tool and does NOT replace clinical    ║
║     or legal professional advice.                                  ║
║                                                                    ║
║  6. Supportive pattern scores analyze TEXT ONLY. Acts of service,  ║
║     quality time, physical affection, and non-verbal cues are NOT  ║
║     captured. A low supportive score does not mean support is      ║
║     absent — it may be expressed through actions, not words.       ║
║                                                                    ║
║  7. "Supportive" text can be manipulative in context (e.g., love  ║
║     bombing). "Negative" text can be reactive self-defense by a   ║
║     victim. Context matters — always consult a professional.       ║
║                                                                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""


def _check_consent(skip: bool = False) -> bool:
    """Display legal notice and obtain user consent on first run.

    Consent is stored in a .consent file in the project root so the
    prompt only appears once. Pass skip=True (or --yes on CLI) to
    bypass for automated/CI runs.
    """
    if skip:
        return True

    # Look for .consent in project root (up one level from engine package)
    consent_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".consent")
    consent_file = os.path.realpath(consent_file)
    if os.path.exists(consent_file):
        return True

    print(_CONSENT_TEXT)  # Keep print for interactive legal notice
    try:
        answer = (
            input("Do you confirm you have legal authority to analyze this data? [y/N]: ")
            .strip()
            .lower()
        )
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return False

    if answer in ("y", "yes"):
        try:
            with open(consent_file, "w") as f:
                f.write(f"Consent given: {datetime.now().isoformat()}\n")
            logger.info("consent_granted", user_confirmed=True)
        except OSError:
            logger.warning("consent_file_error", error="Could not write .consent file")
        return True

    print("\nYou must confirm consent before running the analysis.")
    return False


def main():
    parser = argparse.ArgumentParser(description="Communication Analysis Toolkit")
    parser.add_argument("--config", type=str, help="Path to case config.json")
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip consent prompt (for automated/CI use)"
    )
    parser.add_argument("--json", action="store_true", help="Output logs in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Initialize structured logging
    setup_logging(json_output=args.json, verbose=args.verbose)

    if not _check_consent(skip=args.yes):
        sys.exit(1)

    try:
        run_analysis(args.config)
    except Exception as e:
        logger.exception("analysis_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
