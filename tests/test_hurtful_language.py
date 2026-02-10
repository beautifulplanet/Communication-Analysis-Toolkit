"""
Tests for hurtful language detection — 30 tests.
Covers severe, moderate, mild, and benign classifications.
"""

import pytest
from engine.patterns import is_directed_hurtful


# ==============================================================================
# SEVERE (8 tests)
# ==============================================================================

class TestSevereHurtful:
    """Severe — personal attacks, weaponizing trauma, threats."""

    def test_severe_no_one_will_love_you(self):
        is_h, words, sev = is_directed_hurtful("No one will ever love you", "received")
        assert is_h is True
        assert sev == "severe"

    def test_severe_youll_regret_this(self):
        is_h, words, sev = is_directed_hurtful("You'll regret this", "received")
        assert is_h is True
        assert sev == "severe"

    def test_severe_youre_worthless(self):
        is_h, words, sev = is_directed_hurtful("You're worthless trash", "received")
        assert is_h is True
        assert sev == "severe"

    def test_severe_ill_destroy_you(self):
        is_h, words, sev = is_directed_hurtful("I'll destroy you", "received")
        assert is_h is True
        assert sev == "severe"

    def test_severe_nobody_loves_you(self):
        is_h, words, sev = is_directed_hurtful("Nobody loves you", "received")
        assert is_h is True
        assert sev == "severe"

    def test_severe_deserve_to_suffer(self):
        is_h, words, sev = is_directed_hurtful("You deserve to suffer", "received")
        assert is_h is True
        assert sev == "severe"

    def test_severe_dead_sister(self):
        is_h, words, sev = is_directed_hurtful("Your dead sister would hate you", "received")
        assert is_h is True
        assert sev == "severe"

    def test_severe_never_see_you(self):
        is_h, words, sev = is_directed_hurtful("I'll never see you again", "received")
        assert is_h is True
        assert sev == "severe"


# ==============================================================================
# MODERATE (8 tests)
# ==============================================================================

class TestModerateHurtful:
    """Moderate — directed profanity, insults aimed at the person."""

    def test_moderate_fuck_you(self):
        is_h, words, sev = is_directed_hurtful("Fuck you", "received")
        assert is_h is True
        assert sev == "moderate"

    def test_moderate_youre_stupid(self):
        is_h, words, sev = is_directed_hurtful("You're so stupid", "received")
        assert is_h is True
        assert sev == "moderate"

    def test_moderate_shut_up(self):
        is_h, words, sev = is_directed_hurtful("Shut up already", "received")
        assert is_h is True
        assert sev == "moderate"

    def test_moderate_youre_an_idiot(self):
        is_h, words, sev = is_directed_hurtful("You're an idiot", "received")
        assert is_h is True
        assert sev == "moderate"

    def test_moderate_hate_you(self):
        is_h, words, sev = is_directed_hurtful("I hate you", "received")
        assert is_h is True
        assert sev == "moderate"

    def test_moderate_go_to_hell(self):
        is_h, words, sev = is_directed_hurtful("Go to hell", "received")
        assert is_h is True
        assert sev == "moderate"

    def test_moderate_youre_a_liar(self):
        is_h, words, sev = is_directed_hurtful("You're a liar", "received")
        assert is_h is True
        assert sev == "moderate"

    def test_moderate_cant_stand_you(self):
        is_h, words, sev = is_directed_hurtful("I can't stand you anymore", "received")
        assert is_h is True
        assert sev == "moderate"


# ==============================================================================
# MILD (7 tests)
# ==============================================================================

class TestMildHurtful:
    """Mild — dismissive, contextual profanity in argument context."""

    def test_mild_whatever(self):
        is_h, words, sev = is_directed_hurtful("Whatever, I don't care", "received")
        assert is_h is True
        assert sev == "mild"

    def test_mild_leave_me_alone(self):
        is_h, words, sev = is_directed_hurtful("Leave me alone", "received")
        assert is_h is True
        assert sev == "mild"

    def test_mild_dont_care(self):
        is_h, words, sev = is_directed_hurtful("I don't care about this", "received")
        assert is_h is True
        assert sev == "mild"

    def test_mild_get_lost(self):
        is_h, words, sev = is_directed_hurtful("Get lost", "received")
        assert is_h is True
        assert sev == "mild"

    def test_mild_go_away(self):
        is_h, words, sev = is_directed_hurtful("Go away", "received")
        assert is_h is True
        assert sev == "mild"

    def test_mild_profanity_directed_at_you(self):
        """Mild profanity that mentions 'you' in the same sentence."""
        is_h, words, sev = is_directed_hurtful("This is damn frustrating, you know", "received")
        assert is_h is True
        assert sev == "mild"

    def test_mild_dont_want_to_hear(self):
        is_h, words, sev = is_directed_hurtful("I don't want to hear about it", "received")
        assert is_h is True
        assert sev == "mild"


# ==============================================================================
# BENIGN (7 tests)
# ==============================================================================

class TestBenignHurtful:
    """Messages that should NOT be classified as hurtful."""

    def test_benign_greeting(self):
        is_h, words, sev = is_directed_hurtful("Good morning!", "received")
        assert is_h is False
        assert sev is None

    def test_benign_love_you(self):
        is_h, words, sev = is_directed_hurtful("Love you, have a great day!", "sent")
        assert is_h is False
        assert sev is None

    def test_benign_question(self):
        is_h, words, sev = is_directed_hurtful("What do you want for dinner?", "sent")
        assert is_h is False
        assert sev is None

    def test_benign_thanks(self):
        is_h, words, sev = is_directed_hurtful("Thanks so much for helping!", "sent")
        assert is_h is False
        assert sev is None

    def test_benign_emoji(self):
        is_h, words, sev = is_directed_hurtful("😊❤️", "received")
        assert is_h is False
        assert sev is None

    def test_benign_empty(self):
        is_h, words, sev = is_directed_hurtful("", "received")
        assert is_h is False
        assert sev is None

    def test_benign_none(self):
        is_h, words, sev = is_directed_hurtful(None, "received")
        assert is_h is False
        assert sev is None
