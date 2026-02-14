"""
Tests for DARVO pattern detection: Deny, Attack, Reverse Victim & Offender.
Based on Freyd (1997) — 30 tests.
"""

from engine.patterns import detect_patterns

# ==============================================================================
# DENY PATTERNS (10 tests)
# ==============================================================================

class TestDenyPatterns:
    """Denial patterns — denying something they clearly did or said."""

    def test_deny_never_said_that(self):
        hits = detect_patterns("I never said that", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_didnt_say_that(self):
        hits = detect_patterns("I didn't say that", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_didnt_do_that(self):
        hits = detect_patterns("I didn't do that", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_thats_not_true(self):
        hits = detect_patterns("That's not true", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_thats_not_what_happened(self):
        hits = detect_patterns("That's not what happened", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_that_didnt_happen(self):
        hits = detect_patterns("That didn't happen", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_dont_remember_saying(self):
        hits = detect_patterns("I don't remember saying that at all", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_i_never_did_that(self):
        hits = detect_patterns("I never did that", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_prove_it(self):
        hits = detect_patterns("Oh yeah? Prove it", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_wheres_the_proof(self):
        hits = detect_patterns("Where's the proof?", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_you_got_no_proof(self):
        hits = detect_patterns("You got no proof of that", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    def test_deny_youre_making_that_up(self):
        hits = detect_patterns("You're making that up", "received")
        cats = [h[0] for h in hits]
        assert "deny" in cats

    # ── Benign / no-match ──

    def test_deny_benign_i_said_that(self):
        """Normal statement should not flag denial."""
        hits = detect_patterns("I said that already", "received")
        cats = [h[0] for h in hits]
        assert "deny" not in cats

    def test_deny_benign_whats_for_dinner(self):
        hits = detect_patterns("What's for dinner?", "received")
        assert hits == []


# ==============================================================================
# ATTACK PATTERNS (10 tests)
# ==============================================================================

class TestAttackPatterns:
    """Attack (DARVO) — turning it around to attack the other person."""

    def test_attack_you_always_ruin(self):
        hits = detect_patterns("You always ruin everything", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_you_always_complain(self):
        hits = detect_patterns("You always complain about something", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_you_never_listen(self):
        hits = detect_patterns("You never listen to me", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_you_never_care(self):
        hits = detect_patterns("You never care about my feelings", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_your_fault(self):
        hits = detect_patterns("This is all your fault", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_youre_the_problem(self):
        hits = detect_patterns("You're the problem here", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_what_about_you(self):
        hits = detect_patterns("What about you? You did worse things", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_you_cant_even(self):
        hits = detect_patterns("You can't even do this one simple thing", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_look_at_yourself(self):
        hits = detect_patterns("Look at yourself before criticizing me", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    def test_attack_youre_no_better(self):
        hits = detect_patterns("You're no better than me", "received")
        cats = [h[0] for h in hits]
        assert "attack" in cats

    # ── Attack with validator ──

    def test_attack_you_always_benign_no_match(self):
        """'You always smile' should NOT match because 'smile' is not in the attack validator list."""
        hits = detect_patterns("You always smile at people", "received")
        cats = [h[0] for h in hits]
        assert "attack" not in cats

    def test_attack_you_never_benign_no_match(self):
        """'You never sleep' should NOT match because 'sleep' is not in the validator list."""
        hits = detect_patterns("You never sleep enough", "received")
        cats = [h[0] for h in hits]
        assert "attack" not in cats


# ==============================================================================
# REVERSE VICTIM & OFFENDER PATTERNS (8 tests)
# ==============================================================================

class TestReverseVictimPatterns:
    """Reverse Victim & Offender — making themselves the victim."""

    def test_rv_you_hurt_me(self):
        hits = detect_patterns("You hurt me so much", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" in cats

    def test_rv_you_made_me_feel(self):
        hits = detect_patterns("You made me feel terrible", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" in cats

    def test_rv_because_of_you(self):
        hits = detect_patterns("I'm depressed because of you", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" in cats

    def test_rv_you_did_this_to_me(self):
        hits = detect_patterns("You did this to me, not the other way around", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" in cats

    def test_rv_im_the_victim(self):
        hits = detect_patterns("I'm the real victim here", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" in cats

    def test_rv_youre_abusing_me(self):
        hits = detect_patterns("You're abusing me and you know it", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" in cats

    def test_rv_look_what_youve_done(self):
        hits = detect_patterns("Look what you've done to me", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" in cats

    def test_rv_you_drove_me_to_this(self):
        hits = detect_patterns("You drove me to this", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" in cats

    # ── Benign ──

    def test_rv_benign_you_made_me_laugh(self):
        """Positive emotion should not match reverse victim."""
        hits = detect_patterns("You made me laugh so hard!", "received")
        cats = [h[0] for h in hits]
        assert "reverse_victim" not in cats
