"""
Tests for Bidirectional Analysis & Relationship Health — 30 tests.
Verifies combined positive + negative detection, Gottman ratio,
and health score calculations.
"""

from engine.patterns import detect_patterns
from engine.patterns_supportive import detect_supportive_patterns
from engine.relationship_health import (
    analyze_message_health,
    calculate_gottman_ratio,
    calculate_health_score,
)

# ==============================================================================
# BIDIRECTIONAL DETECTION (10 tests)
# ==============================================================================

class TestBidirectionalDetection:
    """Test that positive and negative patterns are detected independently."""

    def test_negative_only_message(self):
        neg = detect_patterns("I never said that", "received")
        pos = detect_supportive_patterns("I never said that", "received")
        assert len(neg) > 0
        assert len(pos) == 0

    def test_positive_only_message(self):
        neg = detect_patterns("I'm so proud of you", "sent")
        pos = detect_supportive_patterns("I'm so proud of you", "sent")
        assert len(neg) == 0
        assert len(pos) > 0

    def test_neutral_message(self):
        neg = detect_patterns("What time is dinner?", "sent")
        pos = detect_supportive_patterns("What time is dinner?", "sent")
        assert len(neg) == 0
        assert len(pos) == 0

    def test_mixed_message(self):
        """A message can contain both negative and positive signals."""
        msg = "I was wrong to say that, you're too sensitive"
        neg = detect_patterns(msg, "sent")
        pos = detect_supportive_patterns(msg, "sent")
        neg_cats = [h[0] for h in neg]
        pos_cats = [h[0] for h in pos]
        assert "gaslighting" in neg_cats  # "you're too sensitive"
        assert "accountability" in pos_cats  # "I was wrong"

    def test_benign_greeting(self):
        neg = detect_patterns("Good morning!", "sent")
        pos = detect_supportive_patterns("Good morning!", "sent")
        assert neg == []
        assert pos == []

    def test_analyze_message_health_positive(self):
        result = analyze_message_health("I appreciate you so much", "sent")
        assert result['supportive_score'] > 0
        assert result['negative_score'] == 0
        assert result['net_score'] > 0

    def test_analyze_message_health_negative(self):
        result = analyze_message_health("You're crazy and delusional", "received")
        assert result['negative_score'] > 0
        assert result['supportive_score'] == 0
        assert result['net_score'] < 0

    def test_analyze_message_health_neutral(self):
        result = analyze_message_health("Ok see you later", "sent")
        assert result['negative_score'] == 0
        assert result['supportive_score'] == 0
        assert result['net_score'] == 0

    def test_analyze_message_health_empty(self):
        result = analyze_message_health("", "sent")
        assert result['net_score'] == 0

    def test_analyze_message_health_mixed(self):
        result = analyze_message_health("I was wrong, but you always ruin things", "sent")
        assert result['negative_score'] > 0
        assert result['supportive_score'] > 0


# ==============================================================================
# GOTTMAN RATIO (10 tests)
# ==============================================================================

class TestGottmanRatio:

    def _msgs(self, bodies, direction="received"):
        return [{"body": b, "direction": direction} for b in bodies]

    def test_ratio_all_positive(self):
        msgs = self._msgs([
            "I appreciate you",
            "You're amazing",
            "I'm proud of you",
            "Thank you for everything",
            "I believe in you",
        ], direction="sent")
        result = calculate_gottman_ratio(msgs)
        assert result['positive_count'] > 0
        assert result['negative_count'] == 0
        assert result['classification'] == 'healthy'

    def test_ratio_all_negative(self):
        msgs = self._msgs([
            "I never said that",
            "You're too sensitive",
            "That didn't happen",
        ])
        result = calculate_gottman_ratio(msgs)
        assert result['negative_count'] > 0
        assert result['positive_count'] == 0
        assert result['classification'] == 'critical'

    def test_ratio_neutral(self):
        msgs = self._msgs([
            "Hello",
            "How are you",
            "Ok fine",
        ])
        result = calculate_gottman_ratio(msgs)
        assert result['classification'] == 'neutral'

    def test_ratio_healthy_5_to_1(self):
        """5 positives per 1 negative = healthy."""
        msgs = self._msgs([
            "I appreciate you",
            "You're wonderful",
            "Thank you so much",
            "I'm proud of you",
            "I believe in you",
            "I never said that",  # 1 negative
        ])
        # At least 5 positive hits for 1+ negative hits
        result = calculate_gottman_ratio(msgs)
        assert result['positive_count'] >= 5
        assert result['negative_count'] >= 1

    def test_ratio_classification_keys(self):
        msgs = self._msgs(["I love you"], direction="sent")
        result = calculate_gottman_ratio(msgs)
        assert 'ratio' in result
        assert 'classification' in result
        assert 'positive_count' in result
        assert 'negative_count' in result
        assert 'total_messages' in result

    def test_ratio_empty_conversation(self):
        result = calculate_gottman_ratio([])
        assert result['positive_count'] == 0
        assert result['negative_count'] == 0
        assert result['classification'] == 'neutral'

    def test_ratio_single_negative(self):
        msgs = self._msgs(["You're crazy"])
        result = calculate_gottman_ratio(msgs)
        assert result['negative_count'] >= 1
        assert result['ratio'] < 1.0

    def test_ratio_breakdown_populated(self):
        msgs = self._msgs([
            "I appreciate you",
            "I never said that",
        ])
        result = calculate_gottman_ratio(msgs)
        assert len(result['positive_breakdown']) > 0 or len(result['negative_breakdown']) > 0

    def test_ratio_total_messages(self):
        msgs = self._msgs(["Hello", "Hi", "Good morning"])
        result = calculate_gottman_ratio(msgs)
        assert result['total_messages'] == 3

    def test_ratio_mixed_directions(self):
        msgs = [
            {"body": "I appreciate you", "direction": "sent"},
            {"body": "You're too sensitive", "direction": "received"},
            {"body": "Thank you for being here", "direction": "sent"},
        ]
        result = calculate_gottman_ratio(msgs)
        assert result['total_messages'] == 3


# ==============================================================================
# HEALTH SCORE (10 tests)
# ==============================================================================

class TestHealthScore:

    def _msgs(self, bodies, direction="sent"):
        return [{"body": b, "direction": direction} for b in bodies]

    def test_score_healthy_conversation(self):
        msgs = [
            {"body": "I appreciate you so much", "direction": "sent"},
            {"body": "Thank you for being there", "direction": "received"},
            {"body": "You're an amazing person", "direction": "sent"},
            {"body": "I'm so proud of you", "direction": "received"},
            {"body": "I believe in you", "direction": "sent"},
            {"body": "We'll get through this together", "direction": "received"},
            {"body": "I'm here for you", "direction": "sent"},
            {"body": "You mean the world to me", "direction": "received"},
        ]
        result = calculate_health_score(msgs)
        assert result['score'] >= 50
        assert result['grade'] in ('A', 'B')

    def test_score_unhealthy_conversation(self):
        msgs = self._msgs([
            "I never said that",
            "You're too sensitive",
            "That's not what happened",
            "You're crazy",
            "You always ruin everything",
        ])
        result = calculate_health_score(msgs)
        assert result['score'] < 50
        assert result['grade'] in ('D', 'F')

    def test_score_empty(self):
        result = calculate_health_score([])
        assert result['score'] >= 0
        assert result['grade'] in ('A', 'B', 'C', 'D', 'F')

    def test_score_has_recommendations(self):
        msgs = self._msgs(["Hello", "How are you"])
        result = calculate_health_score(msgs)
        assert len(result['recommendations']) > 0

    def test_score_keys(self):
        result = calculate_health_score([])
        assert 'score' in result
        assert 'grade' in result
        assert 'classification' in result
        assert 'gottman_ratio' in result
        assert 'factors' in result
        assert 'recommendations' in result

    def test_score_range_0_to_100(self):
        msgs = self._msgs(["I love you", "You're amazing"])
        result = calculate_health_score(msgs)
        assert 0 <= result['score'] <= 100

    def test_score_factors_breakdown(self):
        msgs = self._msgs(["I appreciate you"])
        result = calculate_health_score(msgs)
        factors = result['factors']
        assert 'ratio_score' in factors
        assert 'diversity_score' in factors
        assert 'severity_score' in factors
        assert 'balance_score' in factors

    def test_grade_a_or_b_for_positive(self):
        msgs = [
            {"body": "I appreciate you", "direction": "sent"},
            {"body": "You're amazing", "direction": "received"},
            {"body": "I believe in you", "direction": "sent"},
            {"body": "Thank you so much", "direction": "received"},
            {"body": "I'm here for you", "direction": "sent"},
            {"body": "I value you", "direction": "received"},
        ]
        result = calculate_health_score(msgs)
        assert result['grade'] in ('A', 'B')

    def test_recommendations_for_high_severity(self):
        msgs = self._msgs([
            "You're crazy and delusional",
            "I'll leave you in the hospital",
            "No one will ever love you",
        ])
        result = calculate_health_score(msgs)
        recs_text = ' '.join(result['recommendations']).lower()
        assert 'professional' in recs_text or 'severity' in recs_text or 'detected' in recs_text

    def test_score_includes_gottman_details(self):
        msgs = self._msgs(["I appreciate you", "You always ruin things"])
        result = calculate_health_score(msgs)
        assert 'details' in result
        assert 'positive_count' in result['details']
        assert 'negative_count' in result['details']
