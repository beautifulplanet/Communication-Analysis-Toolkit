"""
Tests for engine/analyzer.py — Analysis Engine

Covers:
  - Security helpers (escape_md, load_config validation)
  - Data ingestion (phone_match, parse_sms, parse_csv)
  - Report generation (structure, escaping)
  - Path traversal protection
  - JSON size limits
"""

import sys
import os
import json
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.analyzer import (
    escape_md,
    load_config,
    phone_match,
    parse_csv_messages,
    DEFAULT_CONFIG,
)


# =============================================================================
# SECURITY HELPERS
# =============================================================================

class TestEscapeMd:
    """Tests for escape_md() — markdown injection prevention."""

    def test_escapes_asterisks(self):
        assert escape_md("**bold**") == "\\*\\*bold\\*\\*"

    def test_escapes_backticks(self):
        assert escape_md("`code`") == "\\`code\\`"

    def test_escapes_brackets(self):
        assert escape_md("[link](url)") == "\\[link\\]\\(url\\)"

    def test_escapes_hash(self):
        assert escape_md("# heading") == "\\# heading"

    def test_escapes_pipe(self):
        assert escape_md("col1 | col2") == "col1 \\| col2"

    def test_escapes_tilde(self):
        assert escape_md("~strikethrough~") == "\\~strikethrough\\~"

    def test_escapes_angle_bracket(self):
        assert escape_md("> quote") == "\\> quote"

    def test_preserves_normal_text(self):
        text = "Hello, how are you today?"
        assert escape_md(text) == text

    def test_empty_string(self):
        assert escape_md("") == ""

    def test_none_returns_none(self):
        assert escape_md(None) is None

    def test_complex_injection(self):
        """A message body that could break markdown formatting."""
        malicious = "# INJECTED HEADING\n![img](http://evil.com/track.png)"
        escaped = escape_md(malicious)
        assert "\\#" in escaped
        assert "\\!" in escaped
        assert "\\[" in escaped
        assert "\\(" in escaped


# =============================================================================
# PHONE MATCHING
# =============================================================================

class TestPhoneMatch:
    """Tests for phone_match() — phone number suffix matching."""

    def test_basic_match(self):
        assert phone_match("+1-347-837-0839", "3478370839") is True

    def test_no_match(self):
        assert phone_match("+1-555-123-4567", "3478370839") is False

    def test_match_with_formatting(self):
        assert phone_match("(347) 837-0839", "3478370839") is True

    def test_empty_number(self):
        assert phone_match("", "3478370839") is False

    def test_empty_suffix(self):
        assert phone_match("+15551234567", "") is False

    def test_none_number(self):
        assert phone_match(None, "3478370839") is False

    def test_short_suffix(self):
        assert phone_match("+15551234567", "4567") is True


# =============================================================================
# CONFIG LOADING
# =============================================================================

class TestLoadConfig:
    """Tests for load_config() — configuration loading with security checks."""

    def test_load_valid_config(self):
        config = {
            "case_name": "Test Case",
            "user_label": "Alice",
            "contact_label": "Bob",
            "output_dir": "./test_output"
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False,
                                          dir=tempfile.gettempdir()) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            loaded = load_config(config_path)
            assert loaded["case_name"] == "Test Case"
            assert loaded["user_label"] == "Alice"
            assert loaded["contact_label"] == "Bob"
            # Should have defaults filled in
            assert loaded["contact_phone"] == ""
            assert loaded["date_start"]  # Should be auto-filled
            assert loaded["date_end"]
        finally:
            os.unlink(config_path)
            out_dir = os.path.join(tempfile.gettempdir(), "test_output")
            if os.path.isdir(out_dir):
                os.rmdir(out_dir)

    def test_path_traversal_blocked(self):
        """output_dir pointing outside the case directory should be rejected."""
        config = {
            "case_name": "Evil Case",
            "output_dir": "../../etc/evil_output"
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False,
                                          dir=tempfile.gettempdir()) as f:
            json.dump(config, f)
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="escapes case directory"):
                load_config(config_path)
        finally:
            os.unlink(config_path)

    def test_oversized_config_rejected(self):
        """Config file > 10MB should be rejected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False,
                                          dir=tempfile.gettempdir()) as f:
            # Write 11MB of valid-ish JSON
            f.write('{"data": "' + 'x' * (11 * 1024 * 1024) + '"}')
            config_path = f.name

        try:
            with pytest.raises(ValueError, match="too large"):
                load_config(config_path)
        finally:
            os.unlink(config_path)


# =============================================================================
# CSV PARSING
# =============================================================================

class TestParseCsv:
    """Tests for parse_csv_messages()."""

    def test_parse_valid_csv(self):
        csv_content = (
            "datetime,direction,body\n"
            "2025-06-15 14:30:00,sent,Hello how are you?\n"
            "2025-06-15 14:32:00,received,I'm fine thanks\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False,
                                          encoding='utf-8') as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            msgs = parse_csv_messages(csv_path)
            assert len(msgs) == 2
            assert msgs[0]['direction'] == 'sent'
            assert msgs[0]['body'] == 'Hello how are you?'
            assert msgs[1]['direction'] == 'received'
            assert msgs[1]['source'] == 'csv'
        finally:
            os.unlink(csv_path)

    def test_parse_empty_path(self):
        msgs = parse_csv_messages("")
        assert msgs == []

    def test_parse_nonexistent_file(self):
        msgs = parse_csv_messages("/nonexistent/path.csv")
        assert msgs == []


# =============================================================================
# DEFAULT CONFIG
# =============================================================================

class TestDefaultConfig:
    """Verify DEFAULT_CONFIG has no PII."""

    def test_no_real_phone_numbers(self):
        assert DEFAULT_CONFIG["contact_phone"] == ""
        assert DEFAULT_CONFIG["phone_suffix"] == ""

    def test_generic_labels(self):
        assert DEFAULT_CONFIG["user_label"] == "User A"
        assert DEFAULT_CONFIG["contact_label"] == "User B"

    def test_untitled_case(self):
        assert DEFAULT_CONFIG["case_name"] == "Untitled Case"
