"""
================================================================================
Communication Analysis Toolkit — Relationship Health Metrics
================================================================================

Calculate relationship health metrics from bidirectional pattern analysis.
Based on Gottman's research showing that stable relationships maintain
approximately a 5:1 ratio of positive to negative interactions.

REFERENCES:
  1. Gottman, J.M. (1994). "What Predicts Divorce?" — 5:1 ratio finding.
  2. Losada, M. & Heaphy, E. (2004). "The Role of Positivity and
     Connectivity in the Performance of Business Teams." — Positivity ratio
     in high-performing teams.
  3. Fredrickson, B. (2009). "Positivity." — Broaden-and-build theory.

================================================================================
"""

from typing import Any, Optional

from engine.patterns import PATTERN_SEVERITY, detect_patterns
from engine.patterns_supportive import (
    SUPPORTIVE_VALUE,
    detect_supportive_patterns,
)


def analyze_message_health(
    body: str,
    direction: str,
    msg_idx: int = -1,
    all_msgs: Optional[list[Any]] = None,
) -> dict[str, Any]:
    """
    Analyze a single message for both negative and supportive patterns.

    Returns:
        Dict with keys: negative_hits, supportive_hits, net_score
    """
    negative = detect_patterns(body, direction, msg_idx, all_msgs)
    supportive = detect_supportive_patterns(body, direction, msg_idx, all_msgs)

    neg_score = sum(PATTERN_SEVERITY.get(cat, 3) for cat, _, _ in negative)
    pos_score = sum(SUPPORTIVE_VALUE.get(cat, 3) for cat, _, _ in supportive)

    return {
        "negative_hits": negative,
        "supportive_hits": supportive,
        "negative_score": neg_score,
        "supportive_score": pos_score,
        "net_score": pos_score - neg_score,
    }


def calculate_gottman_ratio(
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate a text-based positive-to-negative pattern ratio.

    IMPORTANT: This is inspired by Gottman's 5:1 ratio research (1994) but
    is NOT equivalent to Gottman's original methodology, which measured
    in-person behavioral interactions including tone, facial expressions,
    body language, and non-verbal cues. This metric analyzes text patterns
    only and should be interpreted as a rough indicator of communication
    dynamics in written exchanges, not a clinical diagnostic.

    Thresholds (adapted for text-based detection):
      - ratio >= 5.0 → "healthy" (predominantly positive communication)
      - 3.0 <= ratio < 5.0 → "at_risk" (mixed signals, worth attention)
      - 1.0 <= ratio < 3.0 → "unhealthy" (significant negative patterns)
      - ratio < 1.0 → "critical" (more negative than positive)

    Args:
        messages: List of message dicts with 'body' and 'direction' keys.

    Returns:
        Dict with ratio, classification, counts, and breakdown.
    """
    positive_count = 0
    negative_count = 0
    positive_by_cat: dict[str, int] = {}
    negative_by_cat: dict[str, int] = {}

    for i, msg in enumerate(messages):
        body = msg.get("body", "")
        direction = msg.get("direction", "unknown")

        neg_hits = detect_patterns(body, direction, msg_idx=i, all_msgs=messages)
        pos_hits = detect_supportive_patterns(body, direction, msg_idx=i, all_msgs=messages)

        for cat, _, _ in neg_hits:
            negative_count += 1
            negative_by_cat[cat] = negative_by_cat.get(cat, 0) + 1

        for cat, _, _ in pos_hits:
            positive_count += 1
            positive_by_cat[cat] = positive_by_cat.get(cat, 0) + 1

    # Calculate ratio (avoid division by zero)
    if negative_count == 0:
        ratio = float("inf") if positive_count > 0 else 0.0
    else:
        ratio = positive_count / negative_count

    # Classify
    if negative_count == 0 and positive_count == 0:
        classification = "neutral"
    elif ratio >= 5.0:
        classification = "healthy"
    elif ratio >= 3.0:
        classification = "at_risk"
    elif ratio >= 1.0:
        classification = "unhealthy"
    else:
        classification = "critical"

    return {
        "ratio": ratio,
        "classification": classification,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "total_messages": len(messages),
        "positive_breakdown": positive_by_cat,
        "negative_breakdown": negative_by_cat,
    }


def calculate_health_score(
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate an overall relationship health score (0-100).

    Scoring factors:
      1. Gottman ratio contribution (0-40 points)
      2. Positive pattern diversity (0-20 points)
      3. Absence of high-severity negatives (0-20 points)
      4. Balance between both parties (0-20 points)

    Returns:
        Dict with score, grade, factors breakdown, and recommendations.
    """
    ratio_data = calculate_gottman_ratio(messages)
    ratio = ratio_data["ratio"]

    # Factor 1: Gottman ratio (0-40 points)
    if ratio == float("inf") or ratio >= 5.0:
        ratio_score = 40
    elif ratio >= 3.0:
        ratio_score = int(20 + (ratio - 3.0) * 10)  # 20-40
    elif ratio >= 1.0:
        ratio_score = int(10 + (ratio - 1.0) * 5)  # 10-20
    else:
        ratio_score = int(max(0, ratio * 10))  # 0-10

    # Factor 2: Positive pattern diversity (0-20 points)
    pos_categories = len(ratio_data["positive_breakdown"])
    diversity_score = min(20, pos_categories * 3)  # ~7 categories = 20

    # Factor 3: Absence of high-severity negatives (0-20 points)
    high_sev_cats = {
        cat
        for cat, count in ratio_data["negative_breakdown"].items()
        if PATTERN_SEVERITY.get(cat, 0) >= 8
    }
    if len(high_sev_cats) == 0:
        severity_score = 20
    elif len(high_sev_cats) <= 2:
        severity_score = 10
    else:
        severity_score = 0

    # Factor 4: Balance (0-20 points) — both parties contributing positively
    sent_pos = 0
    recv_pos = 0
    for msg in messages:
        body = msg.get("body", "")
        direction = msg.get("direction", "unknown")
        hits = detect_supportive_patterns(body, direction)
        if direction == "sent":
            sent_pos += len(hits)
        else:
            recv_pos += len(hits)

    total_pos = sent_pos + recv_pos
    if total_pos == 0:
        balance_score = 0
    else:
        minority = min(sent_pos, recv_pos)
        balance_ratio = minority / total_pos  # 0.0 to 0.5
        balance_score = int(balance_ratio * 40)  # 0-20

    total_score = ratio_score + diversity_score + severity_score + balance_score
    total_score = max(0, min(100, total_score))

    # Grade
    if total_score >= 80:
        grade = "A"
    elif total_score >= 65:
        grade = "B"
    elif total_score >= 50:
        grade = "C"
    elif total_score >= 35:
        grade = "D"
    else:
        grade = "F"

    # Recommendations
    recommendations = []
    if ratio_score < 20:
        recommendations.append(
            "Increase positive interactions. Gottman's research shows stable "
            "relationships need at least 5 positive interactions for every negative one."
        )
    if diversity_score < 10:
        recommendations.append(
            "Diversify supportive behaviors. Try validation, encouragement, "
            "appreciation, and active listening to build connection."
        )
    if severity_score < 20:
        high_sev_names = ", ".join(sorted(high_sev_cats))
        recommendations.append(
            f"High-severity patterns detected ({high_sev_names}). "
            "Consider professional support to address these dynamics."
        )
    if balance_score < 10:
        recommendations.append(
            "Supportive communication appears one-sided. Healthy relationships "
            "feature mutual positive engagement from both parties."
        )
    if not recommendations:
        recommendations.append(
            "Communication patterns appear healthy. Continue maintaining "
            "positive interactions and mutual support."
        )

    return {
        "score": total_score,
        "grade": grade,
        "classification": ratio_data["classification"],
        "gottman_ratio": ratio,
        "factors": {
            "ratio_score": ratio_score,
            "diversity_score": diversity_score,
            "severity_score": severity_score,
            "balance_score": balance_score,
        },
        "recommendations": recommendations,
        "details": ratio_data,
    }
