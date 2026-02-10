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
from engine.analyzer import main as run_analysis

__version__ = "3.0.0"
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
    'run_analysis',
]
