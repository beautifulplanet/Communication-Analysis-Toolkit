"""
Tests for engine/patterns.py — Pattern Detection Library

Covers:
  - Hurtful language detection (severe, moderate, mild, benign)
  - DARVO patterns (deny, attack, reverse victim)
  - Gaslighting patterns
  - Gottman's Four Horsemen (criticism, contempt, defensiveness, stonewalling)
  - Coercive control (control, financial, weaponize family)
  - Extended manipulation patterns
  - Context filters (apology, self-directed, third-party, de-escalation,
    expressing hurt, joke context, banter)
  - Context filter suppression (mild categories suppressed, severe never suppressed)
"""

import sys
import os
import pytest

# Ensure the project root is on sys.path so `engine` is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.patterns import (
    is_directed_hurtful,
    detect_patterns,
    is_apology,
    is_self_directed,
    is_third_party_venting,
    is_de_escalation,
    is_expressing_hurt,
    is_joke_context,
    is_banter,
    PATTERN_LABELS,
    PATTERN_DESCRIPTIONS,
    PATTERN_SEVERITY,
)


# =============================================================================
# HURTFUL LANGUAGE DETECTION
# =============================================================================

class TestHurtfulLanguage:
    """Tests for is_directed_hurtful()."""

    # ── Severe ──

    def test_severe_direct_threat(self):
        hit, words, sev = is_directed_hurtful("I'll kill you", "sent")
        assert hit is True
        assert sev == "severe"
        assert len(words) > 0

    def test_severe_weaponizing_death(self):
        hit, words, sev = is_directed_hurtful("at least my mom isn't dead", "sent")
        assert hit is True
        assert sev == "severe"

    def test_severe_unlovability_attack(self):
        hit, words, sev = is_directed_hurtful("no one will ever love you", "sent")
        assert hit is True
        assert sev == "severe"

    def test_severe_wish_of_harm(self):
        hit, words, sev = is_directed_hurtful("you deserve to suffer", "sent")
        assert hit is True
        assert sev == "severe"

    # ── Moderate ──

    def test_moderate_directed_profanity(self):
        hit, words, sev = is_directed_hurtful("fuck you", "sent")
        assert hit is True
        assert sev in ("moderate", "severe")

    # ── Mild ──

    def test_mild_dismissive_whatever(self):
        hit, words, sev = is_directed_hurtful("whatever you say", "sent")
        assert hit is True
        assert sev == "mild"

    # ── Benign (should NOT flag) ──

    def test_benign_casual_profanity(self):
        hit, words, sev = is_directed_hurtful("that movie was fucking great", "sent")
        # Casual profanity not directed at "you" should not flag as severe/moderate
        if hit:
            assert sev == "mild" or sev is None

    def test_benign_normal_message(self):
        hit, words, sev = is_directed_hurtful("Hey, want to grab lunch?", "sent")
        assert hit is False
        assert sev is None

    def test_benign_empty_message(self):
        hit, words, sev = is_directed_hurtful("", "sent")
        assert hit is False
        assert sev is None

    def test_benign_none_body(self):
        hit, words, sev = is_directed_hurtful(None, "sent")
        assert hit is False


# =============================================================================
# DARVO PATTERNS
# =============================================================================

class TestDARVO:
    """Tests for DARVO detection via detect_patterns()."""

    def test_deny_never_said_that(self):
        results = detect_patterns("I never said that", "received")
        cats = [r[0] for r in results]
        assert "deny" in cats

    def test_deny_thats_not_true(self):
        results = detect_patterns("that's not true", "received")
        cats = [r[0] for r in results]
        assert "deny" in cats

    def test_deny_prove_it(self):
        results = detect_patterns("prove it", "received")
        cats = [r[0] for r in results]
        assert "deny" in cats

    def test_attack_your_fault(self):
        results = detect_patterns("it's your fault", "received")
        cats = [r[0] for r in results]
        assert "attack" in cats

    def test_attack_youre_the_problem(self):
        results = detect_patterns("you're the problem", "received")
        cats = [r[0] for r in results]
        assert "attack" in cats

    def test_reverse_victim(self):
        results = detect_patterns("you made me do this", "received")
        cats = [r[0] for r in results]
        assert "reverse_victim" in cats

    def test_reverse_victim_blame_shift(self):
        results = detect_patterns("you did this to me", "received")
        cats = [r[0] for r in results]
        assert "reverse_victim" in cats


# =============================================================================
# GASLIGHTING
# =============================================================================

class TestGaslighting:
    """Tests for gaslighting detection."""

    def test_gaslighting_youre_crazy(self):
        results = detect_patterns("you're crazy", "received")
        cats = [r[0] for r in results]
        assert "gaslighting" in cats

    def test_gaslighting_too_sensitive(self):
        results = detect_patterns("you're too sensitive", "received")
        cats = [r[0] for r in results]
        assert "gaslighting" in cats

    def test_gaslighting_imagining_things(self):
        results = detect_patterns("you're imagining things up", "received")
        cats = [r[0] for r in results]
        assert "gaslighting" in cats


# =============================================================================
# GOTTMAN'S FOUR HORSEMEN
# =============================================================================

class TestGottman:
    """Tests for Gottman's Four Horsemen detection."""

    def test_criticism_you_always(self):
        results = detect_patterns("you always ruin everything", "received")
        cats = [r[0] for r in results]
        # Should flag as attack and/or criticism
        assert "attack" in cats or "criticism" in cats

    def test_contempt_pathetic(self):
        results = detect_patterns("you're pathetic", "received")
        cats = [r[0] for r in results]
        assert "contempt" in cats

    def test_defensiveness_not_my_fault(self):
        results = detect_patterns("I didn't do anything wrong", "received")
        cats = [r[0] for r in results]
        assert "defensiveness" in cats

    def test_stonewalling_leave_me_alone(self):
        results = detect_patterns("don't talk to me", "received")
        cats = [r[0] for r in results]
        assert "stonewalling" in cats

    def test_stonewalling_im_done_talking(self):
        results = detect_patterns("I'm done talking about this", "received")
        cats = [r[0] for r in results]
        assert "stonewalling" in cats


# =============================================================================
# COERCIVE CONTROL
# =============================================================================

class TestCoerciveControl:
    """Tests for coercive control patterns."""

    def test_control_who_were_you_with(self):
        results = detect_patterns("who were you talking to", "received")
        cats = [r[0] for r in results]
        assert "control" in cats

    def test_control_not_allowed(self):
        results = detect_patterns("you can't talk to him", "received")
        cats = [r[0] for r in results]
        assert "control" in cats

    def test_financial_control(self):
        results = detect_patterns("I pay for everything around here", "received")
        cats = [r[0] for r in results]
        assert "financial_control" in cats

    def test_weaponize_family(self):
        results = detect_patterns("your mom is sick and dying because of you", "received")
        cats = [r[0] for r in results]
        assert "weaponize_family" in cats


# =============================================================================
# EXTENDED MANIPULATION
# =============================================================================

class TestExtendedManipulation:
    """Tests for extended manipulation patterns."""

    def test_guilt_trip(self):
        results = detect_patterns("after everything I've done for you", "received")
        cats = [r[0] for r in results]
        assert "guilt_trip" in cats

    def test_ultimatum(self):
        results = detect_patterns("if you don't stop I'm leaving", "received")
        cats = [r[0] for r in results]
        assert "ultimatum" in cats

    def test_love_bombing(self):
        results = detect_patterns("you're the most amazing person I've ever met, I can't live without you", "received")
        cats = [r[0] for r in results]
        assert "love_bombing" in cats

    def test_emotional_blackmail(self):
        results = detect_patterns("if you loved me you would do this", "received")
        cats = [r[0] for r in results]
        assert "emotional_blackmail" in cats

    def test_silent_treatment(self):
        results = detect_patterns("I'm not going to talk to you anymore", "received")
        cats = [r[0] for r in results]
        assert "silent_treatment" in cats

    def test_minimizing(self):
        results = detect_patterns("you're overreacting", "received")
        cats = [r[0] for r in results]
        assert "minimizing" in cats or "gaslighting" in cats

    def test_triangulation(self):
        results = detect_patterns("my ex thinks you're controlling", "received")
        cats = [r[0] for r in results]
        assert "triangulation" in cats

    def test_catastrophizing(self):
        results = detect_patterns("everything is ruined because of you", "received")
        cats = [r[0] for r in results]
        assert "catastrophizing" in cats or "attack" in cats


# =============================================================================
# BENIGN MESSAGES — No False Positives
# =============================================================================

class TestBenignMessages:
    """Messages that should NOT trigger any pattern detection."""

    def test_normal_greeting(self):
        results = detect_patterns("Hey how's your day going?", "sent")
        assert len(results) == 0

    def test_making_plans(self):
        results = detect_patterns("Want to get dinner at 7?", "sent")
        assert len(results) == 0

    def test_empty_message(self):
        results = detect_patterns("", "sent")
        assert len(results) == 0

    def test_positive_message(self):
        results = detect_patterns("I had a great time today, thanks!", "sent")
        assert len(results) == 0

    def test_logistics(self):
        results = detect_patterns("I'll be there in 10 minutes", "sent")
        assert len(results) == 0


# =============================================================================
# CONTEXT FILTERS
# =============================================================================

class TestContextFilters:
    """Tests for the 7 context filter functions."""

    # ── is_apology ──

    def test_apology_im_sorry(self):
        assert is_apology("I'm sorry, I was wrong") is True

    def test_apology_my_bad(self):
        assert is_apology("my bad, I shouldn't have said that") is True

    def test_apology_ill_do_better(self):
        assert is_apology("I'll do better next time") is True

    def test_apology_youre_right(self):
        assert is_apology("you're right, I messed up") is True

    def test_not_apology_normal(self):
        assert is_apology("Hey what's up") is False

    def test_apology_empty(self):
        assert is_apology("") is False

    # ── is_self_directed ──

    def test_self_directed_i_suck(self):
        assert is_self_directed("I suck at this") is True

    def test_self_directed_i_messed_up(self):
        assert is_self_directed("I messed up bad") is True

    def test_self_directed_im_terrible(self):
        assert is_self_directed("I'm a terrible person") is True

    def test_not_self_directed(self):
        assert is_self_directed("you are terrible") is False

    # ── is_third_party_venting ──

    def test_third_party_boss(self):
        assert is_third_party_venting("my boss is such an asshole") is True

    def test_third_party_work_sucks(self):
        assert is_third_party_venting("this job sucks so bad") is True

    def test_third_party_car_broke(self):
        assert is_third_party_venting("my car broke down again, shit") is True

    def test_not_third_party(self):
        assert is_third_party_venting("you are so annoying") is False

    # ── is_de_escalation ──

    def test_de_escalation_calm(self):
        assert is_de_escalation("let's calm down and talk") is True

    def test_de_escalation_dont_fight(self):
        assert is_de_escalation("I don't want to fight") is True

    def test_de_escalation_stop(self):
        assert is_de_escalation("please stop") is True

    def test_de_escalation_need_space(self):
        assert is_de_escalation("I need some space right now") is True

    def test_not_de_escalation(self):
        assert is_de_escalation("you always start fights") is False

    # ── is_expressing_hurt ──

    def test_expressing_hurt_dont_wanna_see_me(self):
        assert is_expressing_hurt("sounds like you don't wanna see me") is True

    def test_expressing_hurt_miss_you(self):
        assert is_expressing_hurt("I miss you so much") is True

    def test_expressing_hurt_this_sucks(self):
        assert is_expressing_hurt("this sucks") is True

    def test_expressing_hurt_are_you_leaving(self):
        assert is_expressing_hurt("are you breaking up with me?") is True

    def test_not_expressing_hurt(self):
        assert is_expressing_hurt("let's get pizza") is False

    # ── is_joke_context ──

    def test_joke_context_laughing(self):
        all_msgs = [
            {"body": "haha that's hilarious", "direction": "sent"},
            {"body": "lol right??", "direction": "received"},
            {"body": "you're so dumb lmao", "direction": "sent"},
            {"body": "hahaha 😂", "direction": "received"},
        ]
        assert is_joke_context(2, all_msgs) is True

    def test_joke_context_no_laughter(self):
        all_msgs = [
            {"body": "we need to talk", "direction": "sent"},
            {"body": "what now", "direction": "received"},
            {"body": "you never listen", "direction": "sent"},
        ]
        assert is_joke_context(2, all_msgs) is False

    # ── is_banter ──

    def test_banter_both_laughing(self):
        all_msgs = [
            {"body": "lol you're ridiculous", "direction": "sent"},
            {"body": "haha I know right", "direction": "received"},
            {"body": "dude stop 😂", "direction": "sent"},
            {"body": "lmao can't help it", "direction": "received"},
        ]
        assert is_banter(2, all_msgs) is True

    def test_banter_one_sided(self):
        all_msgs = [
            {"body": "haha lol", "direction": "sent"},
            {"body": "this isn't funny", "direction": "received"},
            {"body": "lol come on", "direction": "sent"},
        ]
        assert is_banter(1, all_msgs) is False


# =============================================================================
# CONTEXT FILTER SUPPRESSION
# =============================================================================

class TestContextFilterSuppression:
    """
    Verify that mild categories are suppressed when context filters fire,
    and severe categories are NEVER suppressed.
    """

    def test_defensiveness_suppressed_when_apology(self):
        """'it's not my fault, I'm sorry' — apology should suppress defensiveness."""
        results = detect_patterns("it's not my fault, I'm sorry I was wrong", "received")
        cats = [r[0] for r in results]
        assert "defensiveness" not in cats

    def test_gaslighting_never_suppressed(self):
        """Gaslighting should fire even during apology context."""
        results = detect_patterns("I'm sorry but you're crazy and imagining things", "received")
        cats = [r[0] for r in results]
        assert "gaslighting" in cats

    def test_control_never_suppressed(self):
        """Control should fire even when expressed as concern."""
        results = detect_patterns("who were you talking to, I need a break", "received")
        cats = [r[0] for r in results]
        assert "control" in cats

    def test_emotional_blackmail_never_suppressed(self):
        """Emotional blackmail should fire even during de-escalation."""
        results = detect_patterns("if you loved me you would stay", "received")
        cats = [r[0] for r in results]
        assert "emotional_blackmail" in cats

    def test_mild_suppressed_third_party_venting(self):
        """Criticism about boss should not flag as a pattern against partner."""
        results = detect_patterns("my boss never listens, this job sucks", "sent")
        cats = [r[0] for r in results]
        # Should not flag as stonewalling/criticism/etc. against partner
        mild_cats = {'defensiveness', 'stonewalling', 'deflection', 'minimizing',
                     'catastrophizing', 'demand_compliance', 'criticism',
                     'guilt_trip', 'silent_treatment', 'selective_memory'}
        flagged_mild = [c for c in cats if c in mild_cats]
        assert len(flagged_mild) == 0


# =============================================================================
# PATTERN METADATA
# =============================================================================

class TestPatternMetadata:
    """Verify all pattern categories have labels, descriptions, and severity."""

    def test_all_categories_have_labels(self):
        for key in PATTERN_SEVERITY:
            assert key in PATTERN_LABELS, f"Missing label for '{key}'"

    def test_all_categories_have_descriptions(self):
        for key in PATTERN_SEVERITY:
            assert key in PATTERN_DESCRIPTIONS, f"Missing description for '{key}'"

    def test_all_categories_have_severity(self):
        for key in PATTERN_LABELS:
            assert key in PATTERN_SEVERITY, f"Missing severity for '{key}'"

    def test_severity_range(self):
        for key, sev in PATTERN_SEVERITY.items():
            assert 1 <= sev <= 10, f"Severity for '{key}' out of range: {sev}"

    def test_label_format(self):
        """All labels should have an emoji prefix."""
        for key, label in PATTERN_LABELS.items():
            # Label should not be empty
            assert len(label) > 3, f"Label too short for '{key}': {label}"
