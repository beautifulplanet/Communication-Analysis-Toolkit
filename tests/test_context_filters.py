"""
Tests for context filter functions — 40 tests.
Verifies that is_apology, is_self_directed, is_third_party_venting,
is_de_escalation, is_expressing_hurt, is_joke_context, is_banter
correctly classify messages to reduce false positives.
"""

import pytest
from engine.patterns import (
    is_apology,
    is_self_directed,
    is_third_party_venting,
    is_de_escalation,
    is_expressing_hurt,
    is_joke_context,
    is_banter,
    detect_patterns,
)


# ==============================================================================
# is_apology (6 tests)
# ==============================================================================

class TestIsApology:

    def test_apology_im_sorry(self):
        assert is_apology("I'm sorry, I was wrong") is True

    def test_apology_my_bad(self):
        assert is_apology("My bad, I shouldn't have done that") is True

    def test_apology_forgive_me(self):
        assert is_apology("Please forgive me") is True

    def test_apology_i_messed_up(self):
        assert is_apology("I messed up and I know it") is True

    def test_apology_youre_right(self):
        assert is_apology("You're right, I'm sorry") is True

    def test_not_apology_attack(self):
        assert is_apology("You're terrible and you know it") is False

    def test_not_apology_empty(self):
        assert is_apology("") is False

    def test_not_apology_none(self):
        assert is_apology(None) is False


# ==============================================================================
# is_self_directed (6 tests)
# ==============================================================================

class TestIsSelfDirected:

    def test_self_im_an_idiot(self):
        assert is_self_directed("I'm an idiot, I know") is True

    def test_self_i_suck(self):
        assert is_self_directed("I suck at this") is True

    def test_self_my_fault(self):
        assert is_self_directed("It's my fault completely") is True

    def test_self_i_was_wrong(self):
        assert is_self_directed("I was wrong about everything") is True

    def test_not_self_you_suck(self):
        assert is_self_directed("You suck at everything") is False

    def test_not_self_empty(self):
        assert is_self_directed("") is False


# ==============================================================================
# is_third_party_venting (6 tests)
# ==============================================================================

class TestIsThirdPartyVenting:

    def test_third_party_boss(self):
        assert is_third_party_venting("My boss is such a jerk") is True

    def test_third_party_job_sucks(self):
        assert is_third_party_venting("This job sucks so bad") is True

    def test_third_party_car_broke(self):
        assert is_third_party_venting("My car broke down, this is fucked") is True

    def test_third_party_coworker(self):
        assert is_third_party_venting("That coworker is driving me crazy") is True

    def test_not_third_party_direct(self):
        assert is_third_party_venting("You're driving me crazy") is False

    def test_not_third_party_empty(self):
        assert is_third_party_venting("") is False


# ==============================================================================
# is_de_escalation (6 tests)
# ==============================================================================

class TestIsDeEscalation:

    def test_deesc_lets_stop_fighting(self):
        assert is_de_escalation("Let's stop fighting please") is True

    def test_deesc_calm_down(self):
        assert is_de_escalation("Please calm down, I don't want to fight") is True

    def test_deesc_can_we_talk_calmly(self):
        assert is_de_escalation("Can we talk calmly about this?") is True

    def test_deesc_dont_want_to_fight(self):
        assert is_de_escalation("I don't want to fight anymore") is True

    def test_deesc_need_a_break(self):
        assert is_de_escalation("I need a break from this conversation") is True

    def test_not_deesc_keep_fighting(self):
        assert is_de_escalation("I'm going to keep fighting until you admit it") is False


# ==============================================================================
# is_expressing_hurt (6 tests)
# ==============================================================================

class TestIsExpressingHurt:

    def test_hurt_sounds_like_you_dont_want(self):
        assert is_expressing_hurt("Sounds like you don't wanna see me") is True

    def test_hurt_i_miss_you(self):
        assert is_expressing_hurt("I miss you so much") is True

    def test_hurt_this_hurts(self):
        assert is_expressing_hurt("This hurts a lot") is True

    def test_hurt_what_am_i_supposed_to(self):
        assert is_expressing_hurt("What am I supposed to do now?") is True

    def test_hurt_please_dont_leave(self):
        assert is_expressing_hurt("Please don't leave me") is True

    def test_not_hurt_normal(self):
        assert is_expressing_hurt("Want to grab pizza tonight?") is False


# ==============================================================================
# is_joke_context (5 tests)
# ==============================================================================

class TestIsJokeContext:
    """Joke context requires 2+ laughter signals in a window of messages."""

    def _make_convo(self, bodies_and_dirs):
        return [{"body": b, "direction": d} for b, d in bodies_and_dirs]

    def test_joke_context_with_laughter(self):
        msgs = self._make_convo([
            ("lol that's hilarious", "received"),
            ("haha right?? 😂", "sent"),
            ("you're so dumb lmao", "received"),
            ("hahaha 😂", "sent"),
        ])
        assert is_joke_context(2, msgs, window=3) is True

    def test_no_joke_context_serious(self):
        msgs = self._make_convo([
            ("We need to talk", "received"),
            ("About what?", "sent"),
            ("you're so dumb", "received"),
            ("That's not nice", "sent"),
        ])
        assert is_joke_context(2, msgs, window=3) is False

    def test_joke_context_emoji_only(self):
        msgs = self._make_convo([
            ("😂😂😂", "received"),
            ("🤣🤣", "sent"),
            ("you idiot", "received"),
        ])
        assert is_joke_context(2, msgs, window=3) is True

    def test_joke_context_edge_start(self):
        msgs = self._make_convo([
            ("lol that's funny", "received"),
            ("haha", "sent"),
        ])
        assert is_joke_context(0, msgs, window=3) is True

    def test_joke_context_single_laugh_not_enough(self):
        msgs = self._make_convo([
            ("lol", "received"),
            ("you're dumb", "received"),
            ("ok", "sent"),
        ])
        assert is_joke_context(1, msgs, window=3) is False


# ==============================================================================
# is_banter (5 tests)
# ==============================================================================

class TestIsBanter:
    """Banter requires BOTH sides laughing in the window."""

    def _make_convo(self, bodies_and_dirs):
        return [{"body": b, "direction": d} for b, d in bodies_and_dirs]

    def test_banter_both_laughing(self):
        msgs = self._make_convo([
            ("lol that's hilarious", "received"),
            ("haha right?? 😂", "sent"),
            ("you're so dumb lmao", "received"),
            ("hahaha 😂", "sent"),
        ])
        assert is_banter(2, msgs, window=4) is True

    def test_not_banter_one_side_only(self):
        msgs = self._make_convo([
            ("lol", "received"),
            ("lmao", "received"),
            ("you're dumb", "received"),
            ("stop it", "sent"),
        ])
        assert is_banter(2, msgs, window=4) is False

    def test_banter_with_bruh(self):
        msgs = self._make_convo([
            ("bruh what", "received"),
            ("omg 😂", "sent"),
            ("you're ridiculous", "received"),
        ])
        assert is_banter(2, msgs, window=4) is True

    def test_not_banter_serious(self):
        msgs = self._make_convo([
            ("We need to talk", "received"),
            ("What happened?", "sent"),
            ("You never listen", "received"),
        ])
        assert is_banter(2, msgs, window=4) is False

    def test_banter_empty_body(self):
        msgs = self._make_convo([
            (None, "received"),
            ("", "sent"),
            ("hello", "received"),
        ])
        assert is_banter(1, msgs, window=4) is False


# ==============================================================================
# CONTEXT SUPPRESSION INTEGRATION (4 tests)
# ==============================================================================

class TestContextSuppression:
    """Verify that MILD_SKIP_CATEGORIES are suppressed when context filters fire."""

    def test_suppression_apology_blocks_defensiveness(self):
        """Apology context should suppress defensiveness detection."""
        msg = "I'm sorry, it's not my fault, I was wrong about everything"
        hits = detect_patterns(msg, "received")
        cats = [h[0] for h in hits]
        # defensiveness is in MILD_SKIP_CATEGORIES so should be suppressed by apology
        assert "defensiveness" not in cats

    def test_suppression_self_directed_blocks_criticism(self):
        """Self-directed negativity should suppress criticism."""
        msg = "I suck at this, I always do things wrong, I always ruin stuff"
        hits = detect_patterns(msg, "received")
        cats = [h[0] for h in hits]
        assert "criticism" not in cats

    def test_no_suppression_for_gaslighting(self):
        """Gaslighting is NOT in MILD_SKIP_CATEGORIES — should never be suppressed."""
        msg = "I'm sorry but you're crazy and imagining things up"
        hits = detect_patterns(msg, "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_no_suppression_for_control(self):
        """Control is NOT in MILD_SKIP_CATEGORIES — should never be suppressed."""
        msg = "I'm the only one who loves you, nobody else cares"
        hits = detect_patterns(msg, "received")
        cats = [h[0] for h in hits]
        assert "control" in cats
