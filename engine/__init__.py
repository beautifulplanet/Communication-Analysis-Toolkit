"""Communication Analysis Toolkit — Engine Package"""

from engine.analyzer import run_analysis
from engine.patterns import (
    PATTERN_DESCRIPTIONS,
    PATTERN_LABELS,
    PATTERN_SEVERITY,
    detect_patterns,
    # Context filters
    is_apology,
    is_banter,
    is_de_escalation,
    is_directed_hurtful,
    is_expressing_hurt,
    is_joke_context,
    is_self_directed,
    is_third_party_venting,
)
from engine.patterns_supportive import (
    SUPPORTIVE_DESCRIPTIONS,
    SUPPORTIVE_LABELS,
    SUPPORTIVE_VALUE,
    detect_supportive_patterns,
)
from engine.relationship_health import (
    analyze_message_health,
    calculate_gottman_ratio,
    calculate_health_score,
)

__version__ = "3.1.0"
__all__ = [
    "is_directed_hurtful",
    "detect_patterns",
    "PATTERN_LABELS",
    "PATTERN_DESCRIPTIONS",
    "PATTERN_SEVERITY",
    "is_apology",
    "is_self_directed",
    "is_third_party_venting",
    "is_de_escalation",
    "is_expressing_hurt",
    "is_joke_context",
    "is_banter",
    "detect_supportive_patterns",
    "SUPPORTIVE_LABELS",
    "SUPPORTIVE_DESCRIPTIONS",
    "SUPPORTIVE_VALUE",
    "analyze_message_health",
    "calculate_gottman_ratio",
    "calculate_health_score",
    "run_analysis",
]
