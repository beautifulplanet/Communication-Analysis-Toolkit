"""
Tests for end-to-end integration — 10 tests.
Verifies that the full pipeline works correctly with realistic data.
"""

import json
import os
import pytest
from engine.patterns import detect_patterns, is_directed_hurtful, PATTERN_LABELS, PATTERN_SEVERITY


# ==============================================================================
# FULL PIPELINE (6 tests)
# ==============================================================================

class TestFullPipeline:
    """Run detect_patterns + is_directed_hurtful over realistic conversations."""

    @pytest.fixture
    def sample_messages(self):
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_messages.json')
        with open(fixture_path, 'r') as f:
            return json.load(f)

    def test_fixture_loads(self, sample_messages):
        """Fixture file should load and contain messages."""
        assert len(sample_messages) > 0
        assert "body" in sample_messages[0]

    def test_detect_patterns_on_fixture(self, sample_messages):
        """Run detect_patterns on every message — should not crash."""
        all_hits = []
        for i, msg in enumerate(sample_messages):
            hits = detect_patterns(
                msg["body"], msg["direction"],
                msg_idx=i, all_msgs=sample_messages,
            )
            all_hits.extend(hits)
        # The fixture has at least "I never said that" and "you're imagining things up"
        cats = [h[0] for h in all_hits]
        assert "deny" in cats
        assert "gaslighting" in cats

    def test_hurtful_on_fixture(self, sample_messages):
        """Run is_directed_hurtful on every message — should find some hurtful."""
        hurtful_count = 0
        for msg in sample_messages:
            is_h, words, sev = is_directed_hurtful(msg["body"], msg["direction"])
            if is_h:
                hurtful_count += 1
        # "no one will ever love you" should trigger at minimum
        assert hurtful_count >= 1

    def test_joke_context_suppression_in_fixture(self, sample_messages):
        """Banter messages (lol/haha) should suppress mild categories."""
        # Message index 16 is "you're so dumb lmao" surrounded by laughter
        msg = sample_messages[16]
        assert "dumb" in msg["body"].lower()
        # With context, mild categories should be suppressed
        hits = detect_patterns(
            msg["body"], msg["direction"],
            msg_idx=16, all_msgs=sample_messages,
        )
        # Contempt uses "you're so dumb" which is NOT in MILD_SKIP_CATEGORIES
        # so it won't be suppressed, but mild ones would be
        cats = [h[0] for h in hits]
        # The key test: criticism/defensiveness would be suppressed here
        assert "criticism" not in cats
        assert "defensiveness" not in cats

    def test_benign_messages_clean(self, sample_messages):
        """Purely benign messages should produce no pattern hits."""
        benign_indices = [0, 1, 2, 3]  # "Good morning", "I'm doing well", etc.
        for idx in benign_indices:
            msg = sample_messages[idx]
            hits = detect_patterns(msg["body"], msg["direction"])
            assert hits == [], f"Message {idx} '{msg['body']}' should be clean but got: {hits}"


# ==============================================================================
# PATTERN METADATA (4 tests)
# ==============================================================================

class TestPatternMetadata:

    def test_all_categories_have_labels(self):
        """Every category used in detect_patterns should have a label."""
        # Comprehensive message that triggers many categories
        messages = [
            ("I never said that", "deny"),
            ("You're too sensitive", "gaslighting"),
            ("You always ruin everything", "criticism"),
            ("This conversation is over", "stonewalling"),
        ]
        for msg, expected_cat in messages:
            hits = detect_patterns(msg, "received")
            for cat, _, _ in hits:
                assert cat in PATTERN_LABELS, f"Category '{cat}' missing from PATTERN_LABELS"

    def test_all_categories_have_severity(self):
        """Every category should have a severity ranking."""
        for cat in PATTERN_LABELS:
            assert cat in PATTERN_SEVERITY, f"Category '{cat}' missing from PATTERN_SEVERITY"

    def test_severity_ranges(self):
        """Severity values should be between 1 and 10."""
        for cat, sev in PATTERN_SEVERITY.items():
            assert 1 <= sev <= 10, f"Severity for '{cat}' is {sev}, expected 1-10"

    def test_labels_are_strings(self):
        """All labels should be non-empty strings."""
        for cat, label in PATTERN_LABELS.items():
            assert isinstance(label, str), f"Label for '{cat}' is not a string"
            assert len(label) > 0, f"Label for '{cat}' is empty"
