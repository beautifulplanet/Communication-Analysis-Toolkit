"""
Tests for edge cases and boundary conditions — 30 tests.
Covers: empty/None inputs, Unicode, mixed case, long inputs,
special characters, and boundary message lengths.
"""

from engine.patterns import detect_patterns, is_directed_hurtful

# ==============================================================================
# EMPTY / NONE INPUTS (6 tests)
# ==============================================================================

class TestEmptyInputs:

    def test_detect_empty_string(self):
        assert detect_patterns("", "received") == []

    def test_detect_none_body(self):
        """None should be handled gracefully."""
        assert detect_patterns(None, "received") == []

    def test_detect_whitespace_only(self):
        assert detect_patterns("   ", "received") == []

    def test_hurtful_empty(self):
        is_h, _, _ = is_directed_hurtful("", "received")
        assert is_h is False

    def test_hurtful_none(self):
        is_h, _, _ = is_directed_hurtful(None, "received")
        assert is_h is False

    def test_detect_newline_only(self):
        assert detect_patterns("\n\n\n", "received") == []


# ==============================================================================
# UNICODE AND SPECIAL CHARACTERS (6 tests)
# ==============================================================================

class TestUnicode:

    def test_emoji_only(self):
        assert detect_patterns("😊❤️🎉", "received") == []

    def test_pattern_with_emoji(self):
        """Pattern should still match even with emojis around it."""
        hits = detect_patterns("I never said that 😤", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_unicode_quotes(self):
        """Smart/curly quotes should not break patterns."""
        hits = detect_patterns("That\u2019s not what happened", "received")
        cats = [h[0] for h in hits]
        # \u2019 is right quotation mark — regex uses .? so it should match
        assert "deny" in cats or "gaslighting" in cats

    def test_accented_characters(self):
        """Accented characters in otherwise normal text should not crash."""
        result = detect_patterns("Café with André was nice", "received")
        assert isinstance(result, list)

    def test_chinese_characters(self):
        result = detect_patterns("你好世界", "received")
        assert result == []

    def test_mixed_script(self):
        result = detect_patterns("Hello мир 世界", "received")
        assert isinstance(result, list)


# ==============================================================================
# CASE SENSITIVITY (6 tests)
# ==============================================================================

class TestCaseSensitivity:

    def test_uppercase_deny(self):
        hits = detect_patterns("I NEVER SAID THAT", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_mixed_case_gaslighting(self):
        hits = detect_patterns("You're TOO SENSITIVE", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_all_caps_threat(self):
        is_h, _, sev = is_directed_hurtful("I'LL DESTROY YOU", "received")
        assert is_h is True
        assert sev == "severe"

    def test_alternating_case(self):
        hits = detect_patterns("yOu AlWaYs RuIn EvErYtHiNg", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_lowercase_control(self):
        hits = detect_patterns("you can't talk to him anymore", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_title_case_no_false_pos(self):
        hits = detect_patterns("Hello There, How Are You?", "received")
        assert hits == []


# ==============================================================================
# LONG INPUTS (4 tests)
# ==============================================================================

class TestLongInputs:

    def test_very_long_benign(self):
        """A very long message with no patterns should return empty."""
        msg = "Hello there, how are you doing today? " * 200
        result = detect_patterns(msg, "received")
        assert result == []

    def test_pattern_in_long_message(self):
        """Pattern buried in a long message should still be found."""
        msg = "Normal text here. " * 50 + "I never said that. " + "More normal text. " * 50
        hits = detect_patterns(msg, "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_long_hurtful(self):
        msg = "You're worthless " * 100
        is_h, _, sev = is_directed_hurtful(msg, "received")
        assert is_h is True
        assert sev == "severe"

    def test_1000_char_no_crash(self):
        msg = "a" * 1000
        result = detect_patterns(msg, "received")
        assert isinstance(result, list)


# ==============================================================================
# MULTIPLE PATTERNS (4 tests)
# ==============================================================================

class TestMultiplePatterns:

    def test_deny_and_gaslighting(self):
        """A message matching both deny and gaslighting."""
        hits = detect_patterns("That didn't happen, you're imagining things up", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats
        assert "gaslighting" in cats

    def test_attack_and_criticism(self):
        """Attack + criticism in same message."""
        hits = detect_patterns("You always ruin everything, it's your fault", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats or "criticism" in cats

    def test_control_and_ultimatum(self):
        """Control + ultimatum combined."""
        hits = detect_patterns("You can't talk to him or we're done", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats or "ultimatum" in cats

    def test_many_categories_severe_message(self):
        """A severe message should trigger multiple categories."""
        msg = "I never said that, you're crazy, it's your fault, after everything I've done for you"
        hits = detect_patterns(msg, "received")
        assert len(hits) >= 2  # At minimum deny + gaslighting


# ==============================================================================
# DIRECTION PARAMETER (4 tests)
# ==============================================================================

class TestDirectionParam:

    def test_sent_direction(self):
        """Direction='sent' should still detect patterns."""
        hits = detect_patterns("I never said that", "sent")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_received_direction(self):
        hits = detect_patterns("You're too sensitive", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_hurtful_sent(self):
        is_h, _, _ = is_directed_hurtful("Fuck you", "sent")
        assert is_h is True

    def test_hurtful_received(self):
        is_h, _, _ = is_directed_hurtful("Fuck you", "received")
        assert is_h is True
