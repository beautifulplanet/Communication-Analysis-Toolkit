"""
================================================================================
Communication Analysis Toolkit — Configuration Module
================================================================================

Handles case configuration loading, validation, and security helpers used
across the engine.

Extracted from analyzer.py for cleaner separation of concerns.
================================================================================
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any

# ==============================================================================
# SECURITY HELPERS
# ==============================================================================

_MD_ESCAPE_RE = re.compile(r"([\\`*_\{\}\[\]()#+\-.!|>~])")


def escape_md(text: str) -> str:
    """Escape markdown special characters in user-supplied text.

    Prevents markdown injection where message bodies could break report
    formatting or inject headings/links/images.
    """
    if not text:
        return text
    return _MD_ESCAPE_RE.sub(r"\\\1", text)


# ==============================================================================
# CONFIGURATION
# ==============================================================================

DEFAULT_CONFIG = {
    "case_name": "Untitled Case",
    "user_label": "User A",
    "contact_label": "User B",
    "contact_phone": "",
    "phone_suffix": "",
    "sms_xml": "",
    "calls_xml": "",
    "signal_db": "",
    "signal_sent_json": "",
    "manual_signal_json": "",
    "signal_desktop_json": "",
    "output_dir": "./output",
    "date_start": "",
    "date_end": "",
}


def load_config(config_path: str) -> dict[str, Any]:
    """Load case configuration from JSON file."""
    with open(config_path, encoding="utf-8") as f:
        raw = f.read()
        if len(raw) > 10 * 1024 * 1024:  # 10 MB sanity limit
            raise ValueError("Config file too large")
        user_config = json.loads(raw)
    config = {**DEFAULT_CONFIG, **user_config}

    # Default date range: 1 year ago to today
    if not config["date_start"]:
        config["date_start"] = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not config["date_end"]:
        config["date_end"] = datetime.now().strftime("%Y-%m-%d")

    # Path traversal protection: validate output_dir is under the config directory
    config_dir = os.path.realpath(os.path.dirname(config_path))
    output_resolved = os.path.realpath(os.path.join(config_dir, config["output_dir"]))
    if not output_resolved.startswith(config_dir):
        raise ValueError(f"output_dir escapes case directory: {config['output_dir']}")
    config["output_dir"] = output_resolved
    os.makedirs(config["output_dir"], exist_ok=True)
    return config
