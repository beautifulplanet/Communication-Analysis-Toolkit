"""Communication Analysis Toolkit — Engine Package"""
from engine.patterns import (
    is_directed_hurtful,
    detect_patterns,
    PATTERN_LABELS,
    PATTERN_DESCRIPTIONS,
    PATTERN_SEVERITY,
    # Context filters
    is_apology,
    is_self_directed,
    is_third_party_venting,
    is_de_escalation,
    is_expressing_hurt,
    is_joke_context,
    is_banter,
)
from engine.patterns_supportive import (
    detect_supportive_patterns,
    SUPPORTIVE_LABELS,
    SUPPORTIVE_DESCRIPTIONS,
    SUPPORTIVE_VALUE,
)
from engine.relationship_health import (
    analyze_message_health,
    calculate_gottman_ratio,
    calculate_health_score,
)
from engine.analyzer import run_analysis

__version__ = "3.1.0"
__all__ = [
    'is_directed_hurtful',
    'detect_patterns',
    'PATTERN_LABELS',
    'PATTERN_DESCRIPTIONS',
    'PATTERN_SEVERITY',
    'is_apology',
    'is_self_directed',
    'is_third_party_venting',
    'is_de_escalation',
    'is_expressing_hurt',
    'is_joke_context',
    'is_banter',
    'detect_supportive_patterns',
    'SUPPORTIVE_LABELS',
    'SUPPORTIVE_DESCRIPTIONS',
    'SUPPORTIVE_VALUE',
    'analyze_message_health',
    'calculate_gottman_ratio',
    'calculate_health_score',
    'run_analysis',
]
