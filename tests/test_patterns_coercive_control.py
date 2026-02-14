"""
Tests for Coercive Control pattern detection (Stark, 2007; Duluth Model).
Control & isolation, financial control, weaponizing family — 25 tests.
"""

from engine.patterns import detect_patterns

# ==============================================================================
# CONTROL & ISOLATION (10 tests)
# ==============================================================================

class TestControlPatterns:
    """Control — controlling who the person sees, talks to, or where they go."""

    def test_ctrl_cant_talk_to(self):
        hits = detect_patterns("You can't talk to him anymore", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_shouldnt_see(self):
        hits = detect_patterns("You shouldn't talk to her anymore", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_who_were_you_with(self):
        hits = detect_patterns("Who were you with last night?", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_show_me_your_phone(self):
        hits = detect_patterns("Show me your phone right now", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_why_talking_to_him(self):
        hits = detect_patterns("Why were you talking to him?", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_dont_need_friends(self):
        hits = detect_patterns("You don't need friends, you have me", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_only_one_who_loves(self):
        hits = detect_patterns("I'm the only one who loves you", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_choose_me(self):
        hits = detect_patterns("You have to choose me over them", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_send_location(self):
        hits = detect_patterns("Send me your location now", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_need_to_know_where(self):
        hits = detect_patterns("I need to know where you are at all times", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_why_didnt_answer(self):
        hits = detect_patterns("Why didn't you answer my calls?", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    def test_ctrl_need_permission(self):
        hits = detect_patterns("You need my permission to go out", "received")
        cats = [h[0] for h in hits]
        assert "control" in cats

    # ── Benign ──

    def test_ctrl_benign_where_are_you(self):
        """Normal check-in should not flag."""
        hits = detect_patterns("Hey are you almost home?", "received")
        cats = [h[0] for h in hits]
        assert "control" not in cats


# ==============================================================================
# FINANCIAL CONTROL (7 tests)
# ==============================================================================

class TestFinancialControlPatterns:
    """Financial control — using money as weapon or leverage."""

    def test_fin_pay_for_everything(self):
        hits = detect_patterns("I pay for everything around here", "received")
        cats = [h[0] for h in hits]
        assert "financial_control" in cats

    def test_fin_you_cant_afford(self):
        hits = detect_patterns("You can't afford that on your own", "received")
        cats = [h[0] for h in hits]
        assert "financial_control" in cats

    def test_fin_my_money(self):
        hits = detect_patterns("It's my money, I'll spend it how I want", "received")
        cats = [h[0] for h in hits]
        assert "financial_control" in cats

    def test_fin_you_owe_me(self):
        hits = detect_patterns("You owe me for everything I've done", "received")
        cats = [h[0] for h in hits]
        assert "financial_control" in cats

    def test_fin_cut_you_off(self):
        hits = detect_patterns("I'll cut you off if you keep this up", "received")
        cats = [h[0] for h in hits]
        assert "financial_control" in cats

    def test_fin_burden(self):
        hits = detect_patterns("You're a financial burden on me", "received")
        cats = [h[0] for h in hits]
        assert "financial_control" in cats

    def test_fin_without_me_homeless(self):
        hits = detect_patterns("Without me you'd be homeless", "received")
        cats = [h[0] for h in hits]
        assert "financial_control" in cats

    # ── Benign ──

    def test_fin_benign_budgeting(self):
        hits = detect_patterns("Let's make a budget together", "received")
        cats = [h[0] for h in hits]
        assert "financial_control" not in cats


# ==============================================================================
# WEAPONIZE FAMILY / HEALTH (6 tests)
# ==============================================================================

class TestWeaponizeFamilyPatterns:
    """Weaponizing family illness, death, or trauma as leverage."""

    def test_fam_mom_seizure(self):
        hits = detect_patterns("Your mom had another seizure and that's your fault", "received")
        cats = [h[0] for h in hits]
        assert "weaponize_family" in cats

    def test_fam_dad_hospital(self):
        hits = detect_patterns("Your dad is in the hospital because of your stress", "received")
        cats = [h[0] for h in hits]
        assert "weaponize_family" in cats

    def test_fam_dead_sister(self):
        hits = detect_patterns("Your dead sister would be ashamed of you", "received")
        cats = [h[0] for h in hits]
        assert "weaponize_family" in cats

    def test_fam_leave_in_hospital(self):
        hits = detect_patterns("I'll leave you in the hospital next time", "received")
        cats = [h[0] for h in hits]
        assert "weaponize_family" in cats

    def test_fam_end_up_like_dad(self):
        hits = detect_patterns("You're going to end up like your dad", "received")
        cats = [h[0] for h in hits]
        assert "weaponize_family" in cats

    def test_fam_my_mom_isnt(self):
        hits = detect_patterns("At least my mom isn't a drunk", "received")
        cats = [h[0] for h in hits]
        assert "weaponize_family" in cats

    # ── Benign ──

    def test_fam_benign_mom_health(self):
        hits = detect_patterns("I hope your mom feels better soon", "received")
        cats = [h[0] for h in hits]
        assert "weaponize_family" not in cats
