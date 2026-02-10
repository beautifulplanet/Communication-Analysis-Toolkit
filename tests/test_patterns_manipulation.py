"""
Tests for Extended Manipulation pattern detection — 30 tests.
Covers: guilt_trip, deflection, ultimatum, looping, lying_indicator,
minimizing, love_bombing, future_faking, triangulation,
emotional_blackmail, silent_treatment, double_bind, prank_test,
selective_memory, catastrophizing, demand_compliance.
"""

import pytest
from engine.patterns import detect_patterns


# ==============================================================================
# GUILT TRIP (3 tests)
# ==============================================================================

class TestGuiltTripPatterns:

    def test_gt_after_everything(self):
        hits = detect_patterns("After everything I've done for you", "received")
        cats = [h[0] for h in hits]
        assert "guilt_trip" in cats

    def test_gt_nothing_without_me(self):
        hits = detect_patterns("You'd be nothing without me", "received")
        cats = [h[0] for h in hits]
        assert "guilt_trip" in cats

    def test_gt_i_put_up_with(self):
        hits = detect_patterns("I put up with so much from you", "received")
        cats = [h[0] for h in hits]
        assert "guilt_trip" in cats


# ==============================================================================
# DEFLECTION (3 tests)
# ==============================================================================

class TestDeflectionPatterns:

    def test_defl_not_the_point(self):
        hits = detect_patterns("That's not the point we're discussing", "received")
        cats = [h[0] for h in hits]
        assert "deflection" in cats

    def test_defl_remember_when_you(self):
        hits = detect_patterns("Remember when you did the exact same thing?", "received")
        cats = [h[0] for h in hits]
        assert "deflection" in cats

    def test_defl_well_what_about(self):
        hits = detect_patterns("Well what about what you did last week?", "received")
        cats = [h[0] for h in hits]
        assert "deflection" in cats


# ==============================================================================
# ULTIMATUMS (3 tests)
# ==============================================================================

class TestUltimatumPatterns:

    def test_ult_were_done(self):
        hits = detect_patterns("Then we're done", "received")
        cats = [h[0] for h in hits]
        assert "ultimatum" in cats

    def test_ult_this_is_your_last_chance(self):
        hits = detect_patterns("This is your last chance", "received")
        cats = [h[0] for h in hits]
        assert "ultimatum" in cats

    def test_ult_if_you_dont_im_leaving(self):
        hits = detect_patterns("If you don't stop I'm leaving", "received")
        cats = [h[0] for h in hits]
        assert "ultimatum" in cats


# ==============================================================================
# LOOPING / INTERROGATION (3 tests)
# ==============================================================================

class TestLoopingPatterns:

    def test_loop_keep_bringing_it_up(self):
        hits = detect_patterns("I'm going to keep bringing it up", "received")
        cats = [h[0] for h in hits]
        assert "looping" in cats

    def test_loop_ill_keep_asking(self):
        hits = detect_patterns("I'll keep asking until you tell me the truth", "received")
        cats = [h[0] for h in hits]
        assert "looping" in cats

    def test_loop_answer_the_question(self):
        hits = detect_patterns("Just answer the question already", "received")
        cats = [h[0] for h in hits]
        assert "looping" in cats


# ==============================================================================
# LYING INDICATORS (3 tests)
# ==============================================================================

class TestLyingIndicatorPatterns:

    def test_lie_already_told_you(self):
        hits = detect_patterns("I already told you what happened", "received")
        cats = [h[0] for h in hits]
        assert "lying_indicator" in cats

    def test_lie_putting_words(self):
        hits = detect_patterns("You're putting words in my mouth", "received")
        cats = [h[0] for h in hits]
        assert "lying_indicator" in cats

    def test_lie_believe_what_you_want(self):
        hits = detect_patterns("Fine, believe what you want", "received")
        cats = [h[0] for h in hits]
        assert "lying_indicator" in cats


# ==============================================================================
# MINIMIZING (2 tests)
# ==============================================================================

class TestMinimizingPatterns:

    def test_min_not_a_big_deal(self):
        hits = detect_patterns("It's not a big deal, stop whining", "received")
        cats = [h[0] for h in hits]
        assert "minimizing" in cats

    def test_min_get_over_it(self):
        hits = detect_patterns("Just get over it already", "received")
        cats = [h[0] for h in hits]
        assert "minimizing" in cats


# ==============================================================================
# LOVE BOMBING (2 tests)
# ==============================================================================

class TestLoveBombingPatterns:

    def test_lb_youre_my_everything(self):
        hits = detect_patterns("You're my everything, I can't be without you", "received")
        cats = [h[0] for h in hits]
        assert "love_bombing" in cats

    def test_lb_cant_live_without(self):
        hits = detect_patterns("I can't live without you, please don't leave", "received")
        cats = [h[0] for h in hits]
        assert "love_bombing" in cats


# ==============================================================================
# FUTURE FAKING (2 tests)
# ==============================================================================

class TestFutureFakingPatterns:

    def test_ff_promise_ill_change(self):
        hits = detect_patterns("I promise I'll change, just give me time", "received")
        cats = [h[0] for h in hits]
        assert "future_faking" in cats

    def test_ff_it_wont_happen_again(self):
        hits = detect_patterns("It won't happen again, I swear", "received")
        cats = [h[0] for h in hits]
        assert "future_faking" in cats


# ==============================================================================
# TRIANGULATION (2 tests)
# ==============================================================================

class TestTriangulationPatterns:

    def test_tri_my_ex_thinks(self):
        hits = detect_patterns("My ex thinks you're being unreasonable", "received")
        cats = [h[0] for h in hits]
        assert "triangulation" in cats

    def test_tri_at_least_she_didnt(self):
        hits = detect_patterns("At least my ex didn't do this to me", "received")
        cats = [h[0] for h in hits]
        assert "triangulation" in cats


# ==============================================================================
# EMOTIONAL BLACKMAIL (2 tests)
# ==============================================================================

class TestEmotionalBlackmailPatterns:

    def test_eb_if_you_loved_me(self):
        hits = detect_patterns("If you loved me you would stay", "received")
        cats = [h[0] for h in hits]
        assert "emotional_blackmail" in cats

    def test_eb_if_you_leave_ill_hurt(self):
        hits = detect_patterns("If you leave I'll hurt myself", "received")
        cats = [h[0] for h in hits]
        assert "emotional_blackmail" in cats


# ==============================================================================
# SILENT TREATMENT (2 tests)
# ==============================================================================

class TestSilentTreatmentPatterns:

    def test_st_not_talking_to_you(self):
        hits = detect_patterns("I'm not going to talk to you anymore", "received")
        cats = [h[0] for h in hits]
        assert "silent_treatment" in cats

    def test_st_dont_bother_calling(self):
        hits = detect_patterns("Don't bother calling me", "received")
        cats = [h[0] for h in hits]
        assert "silent_treatment" in cats


# ==============================================================================
# DOUBLE BIND (2 tests)
# ==============================================================================

class TestDoubleBind:

    def test_db_cant_win(self):
        hits = detect_patterns("You can't win no matter what you do", "received")
        cats = [h[0] for h in hits]
        assert "double_bind" in cats

    def test_db_nothing_ever_enough(self):
        hits = detect_patterns("Nothing you do is ever good enough for me", "received")
        cats = [h[0] for h in hits]
        assert "double_bind" in cats


# ==============================================================================
# PRANK / TEST (2 tests)
# ==============================================================================

class TestPrankTestPatterns:

    def test_pt_it_was_a_test(self):
        hits = detect_patterns("It was just a test to see what you'd do", "received")
        cats = [h[0] for h in hits]
        assert "prank_test" in cats

    def test_pt_i_was_testing_you(self):
        hits = detect_patterns("I was just testing you", "received")
        cats = [h[0] for h in hits]
        assert "prank_test" in cats


# ==============================================================================
# SELECTIVE MEMORY (2 tests)
# ==============================================================================

class TestSelectiveMemoryPatterns:

    def test_sm_forgot_to_mention(self):
        hits = detect_patterns("I forgot to mention that part", "received")
        cats = [h[0] for h in hits]
        assert "selective_memory" in cats

    def test_sm_didnt_tell_you_because(self):
        hits = detect_patterns("I didn't tell you because I didn't think it mattered", "received")
        cats = [h[0] for h in hits]
        assert "selective_memory" in cats


# ==============================================================================
# CATASTROPHIZING (2 tests)
# ==============================================================================

class TestCatastrophizingPatterns:

    def test_cat_everything_is_ruined(self):
        hits = detect_patterns("Everything is ruined because of this", "received")
        cats = [h[0] for h in hits]
        assert "catastrophizing" in cats

    def test_cat_our_life_is_over(self):
        hits = detect_patterns("Our life is ruined, there's no fixing this", "received")
        cats = [h[0] for h in hits]
        assert "catastrophizing" in cats


# ==============================================================================
# DEMAND COMPLIANCE (2 tests)
# ==============================================================================

class TestDemandCompliancePatterns:

    def test_dc_admit_it(self):
        hits = detect_patterns("Just admit it already", "received")
        cats = [h[0] for h in hits]
        assert "demand_compliance" in cats

    def test_dc_agree_with_me(self):
        hits = detect_patterns("Just agree with me for once", "received")
        cats = [h[0] for h in hits]
        assert "demand_compliance" in cats
