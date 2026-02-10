"""
Tests for Gaslighting pattern detection (Stern, 2007) — 25 tests.
Covers all subcategories: reality denial, sanity questioning,
sensitivity shaming, joke deflection, social consensus weaponizing.
"""

import pytest
from engine.patterns import detect_patterns


class TestGaslightingRealityDenial:
    """Reality denial subcategory."""

    def test_that_never_happened(self):
        hits = detect_patterns("That never happened", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_that_didnt_happen(self):
        hits = detect_patterns("That didn't happen and you know it", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_youre_imagining_things_up(self):
        hits = detect_patterns("You're imagining things up", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_youre_remembering_wrong(self):
        hits = detect_patterns("You're remembering it wrong", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_thats_not_what_happened(self):
        hits = detect_patterns("That's not what happened", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats


class TestGaslightingSanityQuestioning:
    """Sanity questioning subcategory."""

    def test_youre_crazy(self):
        hits = detect_patterns("You're crazy if you believe that", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_youre_delusional(self):
        hits = detect_patterns("You're delusional right now", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_youre_losing_it(self):
        hits = detect_patterns("You're losing it", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_you_need_therapy_because(self):
        hits = detect_patterns("You need therapy because you can't handle anything", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_you_sound_crazy(self):
        hits = detect_patterns("You sound crazy right now", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_something_is_wrong_with_you(self):
        hits = detect_patterns("Something is wrong with you", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_only_one_who_thinks_that(self):
        hits = detect_patterns("You're the only one who thinks that", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats


class TestGaslightingSensitivityShaming:
    """Sensitivity shaming subcategory."""

    def test_youre_too_sensitive(self):
        hits = detect_patterns("You're too sensitive about everything", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_youre_overreacting(self):
        hits = detect_patterns("You're overreacting as usual", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_stop_being_dramatic(self):
        hits = detect_patterns("Stop being so dramatic", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_you_always_twist_things(self):
        hits = detect_patterns("You always twist things around", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_took_it_wrong_way(self):
        hits = detect_patterns("You took it the wrong way", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats


class TestGaslightingJokeDeflection:
    """Joke deflection subcategory."""

    def test_was_just_joking(self):
        hits = detect_patterns("I was just joking, relax", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_cant_you_take_a_joke(self):
        hits = detect_patterns("Can't you take a joke?", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_lighten_up(self):
        hits = detect_patterns("Lighten up, it's not that serious", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_relax_it_was_a_joke(self):
        hits = detect_patterns("Relax, it was just a joke", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats


class TestGaslightingSocialConsensus:
    """Social consensus weaponizing subcategory."""

    def test_no_one_thinks_that(self):
        hits = detect_patterns("No one else thinks that way", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_everyone_thinks_youre(self):
        hits = detect_patterns("Everyone thinks you're being unreasonable", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_ask_anyone(self):
        hits = detect_patterns("Ask anyone, they'll tell you the same thing", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats

    def test_nobody_else_has_problem(self):
        hits = detect_patterns("Nobody else has a problem with this", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" in cats


class TestGaslightingBenign:
    """Messages that should NOT be flagged as gaslighting."""

    def test_benign_are_you_sure(self):
        """'Are you sure?' without question mark may not flag."""
        hits = detect_patterns("Let me know if you're sure", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" not in cats

    def test_benign_normal_suggestion(self):
        hits = detect_patterns("Maybe you should rest a bit", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" not in cats

    def test_benign_asking_opinion(self):
        hits = detect_patterns("What do you think about this?", "received")
        cats = [h[0] for h in hits]
        assert "gaslighting" not in cats
