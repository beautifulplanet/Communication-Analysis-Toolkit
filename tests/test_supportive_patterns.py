"""
Tests for Supportive Pattern Detection — 110 tests.
Covers all 14 supportive categories plus benign/no-match checks.
"""

import pytest
from engine.patterns_supportive import (
    detect_supportive_patterns,
    SUPPORTIVE_LABELS,
    SUPPORTIVE_DESCRIPTIONS,
    SUPPORTIVE_VALUE,
)


# ==============================================================================
# VALIDATION (8 tests)
# ==============================================================================

class TestValidationPatterns:
    """Validation — acknowledging feelings and experiences as valid."""

    def test_val_that_makes_sense(self):
        hits = detect_supportive_patterns("That makes sense, I get it", "sent")
        cats = [h[0] for h in hits]
        assert "validation" in cats

    def test_val_i_understand_why(self):
        hits = detect_supportive_patterns("I understand why you feel that way", "sent")
        cats = [h[0] for h in hits]
        assert "validation" in cats

    def test_val_your_feelings_valid(self):
        hits = detect_supportive_patterns("Your feelings are valid", "sent")
        cats = [h[0] for h in hits]
        assert "validation" in cats

    def test_val_i_get_why(self):
        hits = detect_supportive_patterns("I totally get why you're upset", "sent")
        cats = [h[0] for h in hits]
        assert "validation" in cats

    def test_val_right_to_feel(self):
        hits = detect_supportive_patterns("You have every right to feel angry", "sent")
        cats = [h[0] for h in hits]
        assert "validation" in cats

    def test_val_thats_understandable(self):
        hits = detect_supportive_patterns("That's completely understandable", "sent")
        cats = [h[0] for h in hits]
        assert "validation" in cats

    def test_val_sounds_hard(self):
        hits = detect_supportive_patterns("That sounds really hard", "sent")
        cats = [h[0] for h in hits]
        assert "validation" in cats

    def test_val_i_hear_you(self):
        hits = detect_supportive_patterns("I hear you, that's rough", "sent")
        cats = [h[0] for h in hits]
        assert "validation" in cats


# ==============================================================================
# EMPATHY (8 tests)
# ==============================================================================

class TestEmpathyPatterns:
    """Empathy — showing emotional understanding and compassion."""

    def test_emp_can_imagine(self):
        hits = detect_supportive_patterns("I can imagine how that feels", "sent")
        cats = [h[0] for h in hits]
        assert "empathy" in cats

    def test_emp_must_be_hard(self):
        hits = detect_supportive_patterns("That must be really hard for you", "sent")
        cats = [h[0] for h in hits]
        assert "empathy" in cats

    def test_emp_sorry_youre_going_through(self):
        hits = detect_supportive_patterns("I'm sorry you're going through this", "sent")
        cats = [h[0] for h in hits]
        assert "empathy" in cats

    def test_emp_sorry_that_happened(self):
        hits = detect_supportive_patterns("I'm sorry that happened to you", "sent")
        cats = [h[0] for h in hits]
        assert "empathy" in cats

    def test_emp_must_have_been_painful(self):
        hits = detect_supportive_patterns("That must have been really painful", "sent")
        cats = [h[0] for h in hits]
        assert "empathy" in cats

    def test_emp_heart_goes_out(self):
        hits = detect_supportive_patterns("My heart goes out to you", "sent")
        cats = [h[0] for h in hits]
        assert "empathy" in cats

    def test_emp_wish_i_could_help(self):
        hits = detect_supportive_patterns("I wish I could take away your pain", "sent")
        cats = [h[0] for h in hits]
        assert "empathy" in cats

    def test_emp_sounds_overwhelming(self):
        hits = detect_supportive_patterns("That sounds incredibly overwhelming", "sent")
        cats = [h[0] for h in hits]
        assert "empathy" in cats


# ==============================================================================
# APPRECIATION (8 tests)
# ==============================================================================

class TestAppreciationPatterns:
    """Appreciation — expressing gratitude and recognizing value."""

    def test_app_appreciate_you(self):
        hits = detect_supportive_patterns("I appreciate you so much", "sent")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats

    def test_app_thank_you_for_being(self):
        hits = detect_supportive_patterns("Thank you for being there for me", "sent")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats

    def test_app_grateful_for_you(self):
        hits = detect_supportive_patterns("I'm so grateful for you", "sent")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats

    def test_app_mean_the_world(self):
        hits = detect_supportive_patterns("You mean the world to me", "sent")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats

    def test_app_value_you(self):
        hits = detect_supportive_patterns("I value you and everything you do", "sent")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats

    def test_app_make_life_better(self):
        hits = detect_supportive_patterns("You make my life so much better", "sent")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats

    def test_app_lucky_to_have(self):
        hits = detect_supportive_patterns("I'm so lucky to have you in my life", "sent")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats

    def test_app_dont_take_for_granted(self):
        hits = detect_supportive_patterns("I don't take you for granted", "sent")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats


# ==============================================================================
# ENCOURAGEMENT (8 tests)
# ==============================================================================

class TestEncouragementPatterns:
    """Encouragement — supporting growth and resilience."""

    def test_enc_believe_in_you(self):
        hits = detect_supportive_patterns("I believe in you completely", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_enc_you_can_do_this(self):
        hits = detect_supportive_patterns("You can do this, I know you can", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_enc_proud_of_you(self):
        hits = detect_supportive_patterns("I'm so proud of you", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_enc_doing_great_job(self):
        hits = detect_supportive_patterns("You're doing a great job", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_enc_come_so_far(self):
        hits = detect_supportive_patterns("You've come so far, don't give up", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_enc_keep_going(self):
        hits = detect_supportive_patterns("Keep going, you're almost there", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_enc_stronger_than_you_think(self):
        hits = detect_supportive_patterns("You're stronger than you think", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_enc_you_inspire_me(self):
        hits = detect_supportive_patterns("You inspire me every day", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats


# ==============================================================================
# ACCOUNTABILITY (7 tests)
# ==============================================================================

class TestAccountabilityPatterns:
    """Accountability — taking genuine responsibility."""

    def test_acc_i_was_wrong(self):
        hits = detect_supportive_patterns("I was wrong to say that", "sent")
        cats = [h[0] for h in hits]
        assert "accountability" in cats

    def test_acc_take_responsibility(self):
        hits = detect_supportive_patterns("I take full responsibility for my actions", "sent")
        cats = [h[0] for h in hits]
        assert "accountability" in cats

    def test_acc_my_fault(self):
        hits = detect_supportive_patterns("That was my fault, not yours", "sent")
        cats = [h[0] for h in hits]
        assert "accountability" in cats

    def test_acc_shouldnt_have(self):
        hits = detect_supportive_patterns("I shouldn't have yelled at you", "sent")
        cats = [h[0] for h in hits]
        assert "accountability" in cats

    def test_acc_owe_apology(self):
        hits = detect_supportive_patterns("I owe you an apology", "sent")
        cats = [h[0] for h in hits]
        assert "accountability" in cats

    def test_acc_need_to_do_better(self):
        hits = detect_supportive_patterns("I need to do better for you", "sent")
        cats = [h[0] for h in hits]
        assert "accountability" in cats

    def test_acc_let_you_down(self):
        hits = detect_supportive_patterns("I let you down and I'm sorry", "sent")
        cats = [h[0] for h in hits]
        assert "accountability" in cats


# ==============================================================================
# REPAIR ATTEMPT (8 tests)
# ==============================================================================

class TestRepairAttemptPatterns:
    """Repair attempts — de-escalating and reconnecting during conflict."""

    def test_rep_start_over(self):
        hits = detect_supportive_patterns("Can we start over?", "sent")
        cats = [h[0] for h in hits]
        assert "repair_attempt" in cats

    def test_rep_dont_want_to_fight(self):
        hits = detect_supportive_patterns("I don't want to fight with you", "sent")
        cats = [h[0] for h in hits]
        assert "repair_attempt" in cats

    def test_rep_take_a_breath(self):
        hits = detect_supportive_patterns("Let's take a breather", "sent")
        cats = [h[0] for h in hits]
        assert "repair_attempt" in cats

    def test_rep_same_team(self):
        hits = detect_supportive_patterns("We're on the same team, remember?", "sent")
        cats = [h[0] for h in hits]
        assert "repair_attempt" in cats

    def test_rep_love_you_sorry(self):
        hits = detect_supportive_patterns("I love you and I'm sorry we fought", "sent")
        cats = [h[0] for h in hits]
        assert "repair_attempt" in cats

    def test_rep_miss_us(self):
        hits = detect_supportive_patterns("I miss us being happy together", "sent")
        cats = [h[0] for h in hits]
        assert "repair_attempt" in cats

    def test_rep_not_to_bed_angry(self):
        hits = detect_supportive_patterns("Let's not go to bed angry please", "sent")
        cats = [h[0] for h in hits]
        assert "repair_attempt" in cats

    def test_rep_how_can_i_fix(self):
        hits = detect_supportive_patterns("How can I make this right?", "sent")
        cats = [h[0] for h in hits]
        assert "repair_attempt" in cats


# ==============================================================================
# ACTIVE LISTENING (7 tests)
# ==============================================================================

class TestActiveListeningPatterns:
    """Active listening — demonstrating attentive engagement."""

    def test_al_tell_me_more(self):
        hits = detect_supportive_patterns("Tell me more about what happened", "sent")
        cats = [h[0] for h in hits]
        assert "active_listening" in cats

    def test_al_im_listening(self):
        hits = detect_supportive_patterns("I'm listening, go ahead", "sent")
        cats = [h[0] for h in hits]
        assert "active_listening" in cats

    def test_al_what_do_you_need(self):
        hits = detect_supportive_patterns("What do you need from me right now?", "sent")
        cats = [h[0] for h in hits]
        assert "active_listening" in cats

    def test_al_how_are_you_feeling(self):
        hits = detect_supportive_patterns("How are you feeling about it?", "sent")
        cats = [h[0] for h in hits]
        assert "active_listening" in cats

    def test_al_want_to_understand(self):
        hits = detect_supportive_patterns("I want to understand your perspective", "sent")
        cats = [h[0] for h in hits]
        assert "active_listening" in cats

    def test_al_help_me_understand(self):
        hits = detect_supportive_patterns("Help me understand what you mean", "sent")
        cats = [h[0] for h in hits]
        assert "active_listening" in cats

    def test_al_so_what_youre_saying(self):
        hits = detect_supportive_patterns("So what you're saying is you felt ignored?", "sent")
        cats = [h[0] for h in hits]
        assert "active_listening" in cats


# ==============================================================================
# EMOTIONAL SUPPORT (8 tests)
# ==============================================================================

class TestEmotionalSupportPatterns:
    """Emotional support — being present and available."""

    def test_es_here_for_you(self):
        hits = detect_supportive_patterns("I'm here for you always", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats

    def test_es_not_alone(self):
        hits = detect_supportive_patterns("You're not alone in this", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats

    def test_es_get_through_together(self):
        hits = detect_supportive_patterns("We'll get through this together", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats

    def test_es_got_you(self):
        hits = detect_supportive_patterns("I've got you, don't worry", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats

    def test_es_count_on_me(self):
        hits = detect_supportive_patterns("You can always count on me", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats

    def test_es_always_be_here(self):
        hits = detect_supportive_patterns("I will always be here for you", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats

    def test_es_not_going_anywhere(self):
        hits = detect_supportive_patterns("I'm not going anywhere", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats

    def test_es_dont_face_alone(self):
        hits = detect_supportive_patterns("You don't have to face this alone", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats


# ==============================================================================
# AFFIRMATION (7 tests)
# ==============================================================================

class TestAffirmationPatterns:
    """Affirmation — affirming the person's character and worth."""

    def test_aff_amazing_person(self):
        hits = detect_supportive_patterns("You're an amazing person", "sent")
        cats = [h[0] for h in hits]
        assert "affirmation" in cats

    def test_aff_proud_to_be_with(self):
        hits = detect_supportive_patterns("I'm so proud to be with you", "sent")
        cats = [h[0] for h in hits]
        assert "affirmation" in cats

    def test_aff_make_me_better(self):
        hits = detect_supportive_patterns("You make me a better person", "sent")
        cats = [h[0] for h in hits]
        assert "affirmation" in cats

    def test_aff_you_are_enough(self):
        hits = detect_supportive_patterns("You are enough, just as you are", "sent")
        cats = [h[0] for h in hits]
        assert "affirmation" in cats

    def test_aff_deserve_happiness(self):
        hits = detect_supportive_patterns("You deserve happiness", "sent")
        cats = [h[0] for h in hits]
        assert "affirmation" in cats

    def test_aff_i_admire_you(self):
        hits = detect_supportive_patterns("I admire your courage", "sent")
        cats = [h[0] for h in hits]
        assert "affirmation" in cats

    def test_aff_kind_heart(self):
        hits = detect_supportive_patterns("You have a kind heart", "sent")
        cats = [h[0] for h in hits]
        assert "affirmation" in cats


# ==============================================================================
# COMPROMISE (7 tests)
# ==============================================================================

class TestCompromisePatterns:
    """Compromise — seeking mutually acceptable solutions."""

    def test_com_find_middle_ground(self):
        hits = detect_supportive_patterns("Let's find a middle ground", "sent")
        cats = [h[0] for h in hits]
        assert "compromise" in cats

    def test_com_what_if_we_both(self):
        hits = detect_supportive_patterns("What if we both try harder?", "sent")
        cats = [h[0] for h in hits]
        assert "compromise" in cats

    def test_com_willing_to_compromise(self):
        hits = detect_supportive_patterns("I'm willing to compromise on this", "sent")
        cats = [h[0] for h in hits]
        assert "compromise" in cats

    def test_com_work_this_out(self):
        hits = detect_supportive_patterns("We can work this out together", "sent")
        cats = [h[0] for h in hits]
        assert "compromise" in cats

    def test_com_hear_your_point(self):
        hits = detect_supportive_patterns("I hear your point and it's fair", "sent")
        cats = [h[0] for h in hits]
        assert "compromise" in cats

    def test_com_valid_point(self):
        hits = detect_supportive_patterns("You make a good point about that", "sent")
        cats = [h[0] for h in hits]
        assert "compromise" in cats

    def test_com_respect_your_opinion(self):
        hits = detect_supportive_patterns("I respect your opinion even if I disagree", "sent")
        cats = [h[0] for h in hits]
        assert "compromise" in cats


# ==============================================================================
# BOUNDARY RESPECT (7 tests)
# ==============================================================================

class TestBoundaryRespectPatterns:
    """Boundary respect — respecting autonomy and space."""

    def test_br_take_your_time(self):
        hits = detect_supportive_patterns("Take your time, no rush", "sent")
        cats = [h[0] for h in hits]
        assert "boundary_respect" in cats

    def test_br_whenever_ready(self):
        hits = detect_supportive_patterns("Whenever you're ready, I'll be here", "sent")
        cats = [h[0] for h in hits]
        assert "boundary_respect" in cats

    def test_br_no_pressure(self):
        hits = detect_supportive_patterns("No pressure at all, really", "sent")
        cats = [h[0] for h in hits]
        assert "boundary_respect" in cats

    def test_br_respect_your_space(self):
        hits = detect_supportive_patterns("I respect your space and boundaries", "sent")
        cats = [h[0] for h in hits]
        assert "boundary_respect" in cats

    def test_br_understand_if_you_need(self):
        hits = detect_supportive_patterns("I understand if you need time alone", "sent")
        cats = [h[0] for h in hits]
        assert "boundary_respect" in cats

    def test_br_dont_have_to_explain(self):
        hits = detect_supportive_patterns("You don't have to explain yourself", "sent")
        cats = [h[0] for h in hits]
        assert "boundary_respect" in cats

    def test_br_ill_be_here_when_ready(self):
        hits = detect_supportive_patterns("I'll be here when you're ready to talk", "sent")
        cats = [h[0] for h in hits]
        assert "boundary_respect" in cats


# ==============================================================================
# REASSURANCE (7 tests)
# ==============================================================================

class TestReassurancePatterns:
    """Reassurance — providing comfort and security."""

    def test_rea_i_love_you(self):
        hits = detect_supportive_patterns("I love you so much", "sent")
        cats = [h[0] for h in hits]
        assert "reassurance" in cats

    def test_rea_were_okay(self):
        hits = detect_supportive_patterns("We're going to be okay", "sent")
        cats = [h[0] for h in hits]
        assert "reassurance" in cats

    def test_rea_not_going_anywhere(self):
        hits = detect_supportive_patterns("I'm not going anywhere, I promise", "sent")
        cats = [h[0] for h in hits]
        assert "reassurance" in cats

    def test_rea_doesnt_change_us(self):
        hits = detect_supportive_patterns("This doesn't change how I feel about you", "sent")
        cats = [h[0] for h in hits]
        assert "reassurance" in cats

    def test_rea_can_trust_me(self):
        hits = detect_supportive_patterns("You can trust me with anything", "sent")
        cats = [h[0] for h in hits]
        assert "reassurance" in cats

    def test_rea_always_love_you(self):
        hits = detect_supportive_patterns("I'll always love you no matter what", "sent")
        cats = [h[0] for h in hits]
        assert "reassurance" in cats

    def test_rea_get_through_this(self):
        hits = detect_supportive_patterns("We'll get through this, I know we will", "sent")
        cats = [h[0] for h in hits]
        assert "reassurance" in cats


# ==============================================================================
# GRATITUDE (6 tests)
# ==============================================================================

class TestGratitudePatterns:
    """Gratitude — expressing thankfulness."""

    def test_gra_thank_you(self):
        hits = detect_supportive_patterns("Thank you for everything", "sent")
        cats = [h[0] for h in hits]
        assert "gratitude" in cats

    def test_gra_thanks_so_much(self):
        hits = detect_supportive_patterns("Thanks so much for helping me", "sent")
        cats = [h[0] for h in hits]
        assert "gratitude" in cats

    def test_gra_cant_thank_enough(self):
        hits = detect_supportive_patterns("I can't thank you enough for this", "sent")
        cats = [h[0] for h in hits]
        assert "gratitude" in cats

    def test_gra_youre_the_best(self):
        hits = detect_supportive_patterns("You're the best, honestly", "sent")
        cats = [h[0] for h in hits]
        assert "gratitude" in cats

    def test_gra_means_so_much(self):
        hits = detect_supportive_patterns("That means so much to me", "sent")
        cats = [h[0] for h in hits]
        assert "gratitude" in cats

    def test_gra_really_needed_that(self):
        hits = detect_supportive_patterns("I really needed to hear that", "sent")
        cats = [h[0] for h in hits]
        assert "gratitude" in cats


# ==============================================================================
# VULNERABILITY (7 tests)
# ==============================================================================

class TestVulnerabilityPatterns:
    """Vulnerability — sharing authentic feelings, building trust."""

    def test_vul_im_scared(self):
        hits = detect_supportive_patterns("I'm scared that we might not make it", "sent")
        cats = [h[0] for h in hits]
        assert "vulnerability" in cats

    def test_vul_i_need_you(self):
        hits = detect_supportive_patterns("I need you right now", "sent")
        cats = [h[0] for h in hits]
        assert "vulnerability" in cats

    def test_vul_be_honest(self):
        hits = detect_supportive_patterns("I have to be honest with you about something", "sent")
        cats = [h[0] for h in hits]
        assert "vulnerability" in cats

    def test_vul_hard_to_say(self):
        hits = detect_supportive_patterns("This is hard for me to say but I need to", "sent")
        cats = [h[0] for h in hits]
        assert "vulnerability" in cats

    def test_vul_feel_insecure(self):
        hits = detect_supportive_patterns("I feel insecure sometimes and I'm working on it", "sent")
        cats = [h[0] for h in hits]
        assert "vulnerability" in cats

    def test_vul_i_trust_you(self):
        hits = detect_supportive_patterns("I trust you with this secret", "sent")
        cats = [h[0] for h in hits]
        assert "vulnerability" in cats

    def test_vul_can_i_be_honest(self):
        hits = detect_supportive_patterns("Can I be honest with you about how I feel?", "sent")
        cats = [h[0] for h in hits]
        assert "vulnerability" in cats


# ==============================================================================
# BENIGN / NO-MATCH (8 tests)
# ==============================================================================

class TestSupportiveBenign:
    """Messages that should NOT trigger supportive patterns."""

    def test_benign_weather(self):
        hits = detect_supportive_patterns("It's sunny outside today", "sent")
        assert hits == []

    def test_benign_logistics(self):
        hits = detect_supportive_patterns("Pick up milk on the way home", "sent")
        assert hits == []

    def test_benign_empty(self):
        hits = detect_supportive_patterns("", "sent")
        assert hits == []

    def test_benign_none(self):
        hits = detect_supportive_patterns(None, "sent")
        assert hits == []

    def test_benign_short_ok(self):
        hits = detect_supportive_patterns("ok", "sent")
        assert hits == []

    def test_benign_question(self):
        hits = detect_supportive_patterns("What time is dinner?", "sent")
        assert hits == []

    def test_benign_neutral_statement(self):
        hits = detect_supportive_patterns("I went to the store earlier", "sent")
        assert hits == []

    def test_benign_emoji_only(self):
        hits = detect_supportive_patterns("👍", "sent")
        assert hits == []


# ==============================================================================
# METADATA TESTS (4 tests)
# ==============================================================================

class TestSupportiveMetadata:

    def test_all_categories_have_labels(self):
        for cat in SUPPORTIVE_VALUE:
            assert cat in SUPPORTIVE_LABELS, f"Missing label for '{cat}'"

    def test_all_categories_have_descriptions(self):
        for cat in SUPPORTIVE_VALUE:
            assert cat in SUPPORTIVE_DESCRIPTIONS, f"Missing description for '{cat}'"

    def test_values_in_range(self):
        for cat, val in SUPPORTIVE_VALUE.items():
            assert 1 <= val <= 10, f"Value for '{cat}' is {val}, expected 1-10"

    def test_labels_are_strings(self):
        for cat, label in SUPPORTIVE_LABELS.items():
            assert isinstance(label, str) and len(label) > 0


# ==============================================================================
# EDGE CASES (4 tests)
# ==============================================================================

class TestSupportiveEdgeCases:

    def test_uppercase(self):
        hits = detect_supportive_patterns("I'M HERE FOR YOU ALWAYS", "sent")
        cats = [h[0] for h in hits]
        assert "emotional_support" in cats

    def test_mixed_case(self):
        hits = detect_supportive_patterns("I Believe In You", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_with_emoji(self):
        hits = detect_supportive_patterns("I'm proud of you ❤️🎉", "sent")
        cats = [h[0] for h in hits]
        assert "encouragement" in cats

    def test_direction_received(self):
        """Supportive patterns should detect from received messages too."""
        hits = detect_supportive_patterns("I appreciate you so much", "received")
        cats = [h[0] for h in hits]
        assert "appreciation" in cats
