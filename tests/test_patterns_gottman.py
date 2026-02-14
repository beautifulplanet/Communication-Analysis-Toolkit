"""
Tests for Gottman's Four Horsemen pattern detection (Gottman & Silver, 1999).
Criticism, Contempt, Defensiveness, Stonewalling — 30 tests.
"""

from engine.patterns import detect_patterns

# ==============================================================================
# CRITICISM (8 tests)
# ==============================================================================

class TestCriticismPatterns:
    """Criticism — attacking character rather than addressing behavior."""

    def test_crit_you_always_do(self):
        hits = detect_patterns("You always do this to me", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_crit_you_always_ruin(self):
        hits = detect_patterns("You always ruin our plans", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_crit_you_never_listen(self):
        hits = detect_patterns("You never listen to anyone", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_crit_you_never_help(self):
        hits = detect_patterns("You never help around the house", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_crit_whats_wrong_with_you(self):
        hits = detect_patterns("What's wrong with you?", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_crit_just_like_your_mom(self):
        hits = detect_patterns("You're just like your mom", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_crit_cant_do_anything_right(self):
        hits = detect_patterns("You can't do anything right", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_crit_youre_impossible(self):
        hits = detect_patterns("You're impossible to deal with", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    def test_crit_always_have_to_be_right(self):
        hits = detect_patterns("You always have to be right", "received")
        cats = [h[0] for h in hits]
        assert "criticism" in cats

    # ── Benign ──

    def test_crit_benign_constructive(self):
        hits = detect_patterns("I felt hurt when you forgot our plans", "received")
        cats = [h[0] for h in hits]
        assert "criticism" not in cats


# ==============================================================================
# CONTEMPT (8 tests)
# ==============================================================================

class TestContemptPatterns:
    """Contempt — treating with disrespect, mockery, superiority."""

    def test_contempt_youre_so_stupid(self):
        hits = detect_patterns("You're so stupid sometimes", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    def test_contempt_grow_up(self):
        hits = detect_patterns("Just grow up already", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    def test_contempt_act_your_age(self):
        hits = detect_patterns("Act your age for once", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    def test_contempt_what_are_you_5(self):
        hits = detect_patterns("What are you, 5 years old?", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    def test_contempt_dumbest_thing(self):
        hits = detect_patterns("That's the dumbest thing I've ever heard", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    def test_contempt_pathetic(self):
        hits = detect_patterns("You are truly pathetic", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    def test_contempt_not_smart_enough(self):
        hits = detect_patterns("You're not smart enough to understand", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    def test_contempt_embarrassed_with_you(self):
        hits = detect_patterns("I can't believe I'm with you", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    def test_contempt_obviously_you(self):
        hits = detect_patterns("Obviously you don't get it", "received")
        cats = [h[0] for h in hits]
        assert "contempt" in cats

    # ── Benign ──

    def test_contempt_benign_grow_plants(self):
        hits = detect_patterns("I want to grow some tomatoes in the garden", "received")
        cats = [h[0] for h in hits]
        assert "contempt" not in cats


# ==============================================================================
# DEFENSIVENESS (7 tests)
# ==============================================================================

class TestDefensivenessPatterns:
    """Defensiveness — deflecting responsibility, counter-blaming."""

    def test_def_didnt_do_anything(self):
        hits = detect_patterns("I didn't do anything wrong, leave me alone", "received")
        cats = [h[0] for h in hits]
        assert "defensiveness" in cats

    def test_def_didnt_do_anything_wrong(self):
        hits = detect_patterns("I didn't do anything wrong", "received")
        cats = [h[0] for h in hits]
        assert "defensiveness" in cats

    def test_def_why_attacking_me(self):
        hits = detect_patterns("Why are you attacking me?", "received")
        cats = [h[0] for h in hits]
        assert "defensiveness" in cats

    def test_def_you_started_it(self):
        hits = detect_patterns("You started it, don't blame me", "received")
        cats = [h[0] for h in hits]
        assert "defensiveness" in cats

    def test_def_what_about_when_you(self):
        hits = detect_patterns("What about when you did the same thing?", "received")
        cats = [h[0] for h in hits]
        assert "defensiveness" in cats

    def test_def_yeah_but_you(self):
        hits = detect_patterns("Yeah but you were worse", "received")
        cats = [h[0] for h in hits]
        assert "defensiveness" in cats

    def test_def_if_you_hadnt(self):
        hits = detect_patterns("If you hadn't provoked me none of this would've happened", "received")
        cats = [h[0] for h in hits]
        assert "defensiveness" in cats

    # ── Benign ──

    def test_def_benign_question(self):
        hits = detect_patterns("What should we have for dinner?", "received")
        cats = [h[0] for h in hits]
        assert "defensiveness" not in cats


# ==============================================================================
# STONEWALLING (7 tests)
# ==============================================================================

class TestStonewallingPatterns:
    """Stonewalling — withdrawing, shutting down, refusal to engage."""

    def test_stone_not_talking_about_this(self):
        hits = detect_patterns("I'm not going to talk about this", "received")
        cats = [h[0] for h in hits]
        assert "stonewalling" in cats

    def test_stone_conversation_over(self):
        hits = detect_patterns("This conversation is over", "received")
        cats = [h[0] for h in hits]
        assert "stonewalling" in cats

    def test_stone_nothing_to_say(self):
        hits = detect_patterns("I have nothing to say", "received")
        cats = [h[0] for h in hits]
        assert "stonewalling" in cats

    def test_stone_done_talking(self):
        hits = detect_patterns("I'm done talking", "received")
        cats = [h[0] for h in hits]
        assert "stonewalling" in cats

    def test_stone_dont_talk_to_me(self):
        hits = detect_patterns("Don't talk to me right now", "received")
        cats = [h[0] for h in hits]
        assert "stonewalling" in cats

    def test_stone_not_listening(self):
        hits = detect_patterns("I'm not listening to this anymore", "received")
        cats = [h[0] for h in hits]
        assert "stonewalling" in cats

    def test_stone_talk_to_wall(self):
        hits = detect_patterns("Talk to the wall because I'm done", "received")
        cats = [h[0] for h in hits]
        assert "stonewalling" in cats

    # ── Benign ──

    def test_stone_benign_good_talk(self):
        hits = detect_patterns("That was a great conversation!", "received")
        cats = [h[0] for h in hits]
        assert "stonewalling" not in cats
