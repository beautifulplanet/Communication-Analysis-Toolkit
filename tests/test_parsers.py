"""
Tests for parsers and security helpers — 20 tests.
Covers: escape_md, load_config, phone_match, parse_sms,
parse_json_messages, and security guardrails.
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from engine.config import escape_md, load_config
from engine.ingestion import parse_json_messages, parse_sms, phone_match

# ==============================================================================
# escape_md (5 tests)
# ==============================================================================

class TestEscapeMd:

    def test_escape_backticks(self):
        assert escape_md("code `here`") == r"code \`here\`"

    def test_escape_asterisks(self):
        assert escape_md("**bold**") == r"\*\*bold\*\*"

    def test_escape_brackets(self):
        assert escape_md("[link](url)") == r"\[link\]\(url\)"

    def test_escape_empty(self):
        assert escape_md("") == ""

    def test_escape_none(self):
        assert escape_md(None) is None

    def test_escape_plain_text(self):
        assert escape_md("hello world") == "hello world"

    def test_escape_hash(self):
        assert escape_md("# heading") == r"\# heading"


# ==============================================================================
# phone_match (4 tests)
# ==============================================================================

class TestPhoneMatch:

    def test_exact_suffix(self):
        assert phone_match("+15551234567", "1234567") is True

    def test_no_match(self):
        assert phone_match("+15559999999", "1234567") is False

    def test_empty_number(self):
        assert phone_match("", "1234567") is False

    def test_empty_suffix(self):
        assert phone_match("+15551234567", "") is False


# ==============================================================================
# load_config (5 tests)
# ==============================================================================

class TestLoadConfig:

    def test_load_valid_config(self):
        """Load a valid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir='.') as f:
            json.dump({"case_name": "Test", "output_dir": "./output"}, f)
            f.flush()
            config = load_config(f.name)
        assert config["case_name"] == "Test"
        os.unlink(f.name)

    def test_load_config_defaults(self):
        """Missing keys should get defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir='.') as f:
            json.dump({"case_name": "Minimal"}, f)
            f.flush()
            config = load_config(f.name)
        assert config["user_label"] == "User A"
        assert config["contact_label"] == "User B"
        os.unlink(f.name)

    def test_load_config_path_traversal(self):
        """output_dir that escapes case directory should raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir='.') as f:
            json.dump({"output_dir": "../../etc/evil"}, f)
            f.flush()
            with pytest.raises(ValueError, match="escapes case directory"):
                load_config(f.name)
        os.unlink(f.name)

    def test_load_config_too_large(self):
        """Config file exceeding 10MB should raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir='.') as f:
            # Write a valid JSON that's very large
            big = {"data": "x" * (11 * 1024 * 1024)}
            json.dump(big, f)
            f.flush()
            with pytest.raises(ValueError, match="too large"):
                load_config(f.name)
        os.unlink(f.name)

    def test_load_config_date_defaults(self):
        """date_start and date_end should get defaults when not provided."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir='.') as f:
            json.dump({"case_name": "DateTest"}, f)
            f.flush()
            config = load_config(f.name)
        assert config["date_start"] != ""
        assert config["date_end"] != ""
        os.unlink(f.name)


# ==============================================================================
# parse_sms (2 tests)
# ==============================================================================

class TestParseSms:

    def test_parse_sms_empty_path(self):
        """Empty path should return empty list."""
        assert parse_sms("", {}) == []

    def test_parse_sms_missing_file(self):
        """Missing file should return empty list gracefully."""
        result = parse_sms("nonexistent_file.xml", {"phone_suffix": "1234"})
        assert result == []


# ==============================================================================
# parse_json_messages (4 tests)
# ==============================================================================

class TestParseJsonMessages:

    def test_parse_json_empty_path(self):
        assert parse_json_messages("") == []

    def test_parse_json_missing_file(self):
        assert parse_json_messages("nonexistent.json") == []

    def test_parse_json_valid(self):
        """Parse a valid JSON messages file."""
        data = {
            "messages": [
                {
                    "body": "Hello!",
                    "direction": "sent",
                    "datetime": "2025-06-01 09:00:00",
                },
                {
                    "body": "Hi there!",
                    "direction": "received",
                    "datetime": "2025-06-01 09:05:00",
                },
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            f.flush()
            result = parse_json_messages(f.name)
        assert len(result) == 2
        assert result[0]["body"] == "Hello!"
        assert result[1]["direction"] == "received"
        os.unlink(f.name)

    def test_parse_json_oversized(self):
        """File over 500MB should be skipped (we test the check, not actual 500MB file)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{}")
            f.flush()
            # Mock os.path.getsize to return a huge value
            with patch('engine.ingestion.os.path.getsize', return_value=600 * 1024 * 1024):
                result = parse_json_messages(f.name)
        assert result == []
        os.unlink(f.name)
