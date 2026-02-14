"""
================================================================================
Communication Analysis Toolkit — Supportive Pattern Detection
================================================================================

Positive communication patterns based on peer-reviewed relationship research:

SOURCES & REFERENCES:
  1. Gottman, J.M. & Silver, N. (1999). "The Seven Principles for Making
     Marriage Work." Harmony Books. — 5:1 positive-to-negative ratio,
     repair attempts, emotional bids, and turning toward.
  2. Johnson, S. (2008). "Hold Me Tight: Seven Conversations for a Lifetime
     of Love." Little, Brown. — Emotionally Focused Therapy (EFT),
     accessibility, responsiveness, engagement (A.R.E.).
  3. Chapman, G. (1992). "The 5 Love Languages." Northfield Publishing.
     — Words of affirmation, quality time, acts of service.
  4. Rogers, C. (1961). "On Becoming a Person." Houghton Mifflin.
     — Unconditional positive regard, empathic listening, genuineness.
  5. Rosenberg, M. (2003). "Nonviolent Communication." PuddleDancer Press.
     — Observation, feeling, need, request framework.
  6. Brown, B. (2012). "Daring Greatly." Gotham Books.
     — Vulnerability, empathy, shame resilience.

SUPPORTIVE CATEGORIES:
  Gottman — Turning Toward:
    validation, repair_attempt, appreciation, fondness

  Emotionally Focused (Johnson, EFT):
    empathy, emotional_support, vulnerability

  Communication Skills (Rogers, Rosenberg):
    active_listening, accountability, compromise

  Affirmation & Encouragement (Chapman):
    encouragement, affirmation, gratitude

  Healthy Boundaries:
    boundary_respect, reassurance

================================================================================
"""

import re
from typing import Dict, List, Optional, Tuple

# Type alias: (supportive_category, matched_text, full_message)
SupportiveMatch = Tuple[str, str, str]


# ==============================================================================
# SECTION 1: VALIDATION (Gottman — Turning Toward)
# ==============================================================================

VALIDATION_PATTERNS = [
    r"\bthat\s+makes\s+sense\b",
    r"\bi\s+(can\s+)?understand\s+(why|how|that|what)\b",
    r"\byour\s+feelings\s+are\s+valid\b",
    r"\bi\s+(totally\s+|completely\s+)?get\s+(why|how|that|it)\b",
    r"\byou\s+have\s+every\s+right\s+to\s+(feel|be)\b",
    r"\bthat.?s\s+(completely\s+|totally\s+)?(understandable|reasonable|fair|valid)\b",
    r"\bi\s+would\s+(feel|think|react)\s+the\s+same\s+(way)?\b",
    r"\bi\s+see\s+(where|why|how)\s+you.?re\s+coming\s+from\b",
    r"\bthat\s+sounds\s+(really\s+)?(hard|tough|difficult|frustrating|stressful)\b",
    r"\bi\s+hear\s+you\b",
]


# ==============================================================================
# SECTION 2: EMPATHY (Johnson, EFT — Accessibility & Responsiveness)
# ==============================================================================

EMPATHY_PATTERNS = [
    r"\bi\s+can\s+(only\s+)?imagine\s+how\s+(that|you)\b",
    r"\bthat\s+must\s+(be|have\s+been)\s+(really\s+)?(hard|tough|difficult|painful|scary|overwhelming|awful|terrible|stressful)\b",
    r"\bi.?m\s+(so\s+)?sorry\s+(you.?re|you\s+are|you\s+had\s+to|that\s+happened|to\s+hear)\b",
    r"\bi\s+(can\s+)?feel\s+(how|your)\b",
    r"\bmy\s+heart\s+(goes|breaks|aches|hurts)\s+(out\s+)?(for|with|to)\s+you\b",
    r"\bi\s+wish\s+i\s+could\s+(take|make)\s+(away|it\s+better)\b",
    r"\bthat\s+sounds\s+(incredibly\s+|really\s+)?(painful|heartbreaking|overwhelming)\b",
]


# ==============================================================================
# SECTION 3: APPRECIATION (Gottman — Fondness & Admiration)
# ==============================================================================

APPRECIATION_PATTERNS = [
    r"\bi\s+appreciate\s+(you|that|everything|what\s+you)\b",
    r"\bthank\s+you\s+(so\s+much\s+)?for\s+(being|doing|helping|listening|understanding|supporting|always|everything|your)\b",
    r"\bi.?m\s+(so\s+)?(thankful|grateful)\s+(for\s+you|to\s+have|that\s+you)\b",
    r"\byou\s+mean\s+(so\s+much|the\s+world|everything)\s+to\s+me\b",
    r"\bi\s+don.?t\s+(take|want\s+to\s+take)\s+you\s+for\s+granted\b",
    r"\bi\s+value\s+(you|your|our|what\s+you|this)\b",
    r"\byou\s+make\s+(my\s+)?life\s+(so\s+much\s+)?better\b",
    r"\bi.?m\s+(so\s+)?lucky\s+to\s+have\s+you\b",
]


# ==============================================================================
# SECTION 4: ENCOURAGEMENT (Chapman — Words of Affirmation)
# ==============================================================================

ENCOURAGEMENT_PATTERNS = [
    r"\bi\s+believe\s+in\s+you\b",
    r"\byou\s+(can|got)\s+(do|handle|get\s+through)\s+(this|it)\b",
    r"\bi.?m\s+(so\s+)?proud\s+of\s+(you|what\s+you)\b",
    r"\byou.?re\s+(doing|handling)\s+(a\s+)?(great|amazing|wonderful|good|fantastic)\s*(job)?\b",
    r"\byou.?ve\s+(come|grown|improved)\s+so\s+(far|much)\b",
    r"\bi\s+know\s+(you\s+can|it.?s\s+hard|this\s+is\s+tough)\b",
    r"\bkeep\s+(going|it\s+up|pushing|trying)\b",
    r"\byou.?re\s+(stronger|braver|smarter|more\s+capable)\s+than\s+you\s+(think|know|realize)\b",
    r"\byou\s+should\s+be\s+proud\s+of\s+(yourself|what\s+you)\b",
    r"\byou\s+inspire\s+me\b",
]


# ==============================================================================
# SECTION 5: ACCOUNTABILITY (Healthy Ownership)
# ==============================================================================

ACCOUNTABILITY_PATTERNS = [
    r"\bi\s+was\s+wrong\b",
    r"\bi\s+take\s+(full\s+)?responsibility\b",
    r"\bthat\s+was\s+my\s+(fault|mistake|bad)\b",
    r"\bi\s+shouldn.?t\s+have\s+(said|done|acted|reacted|yelled|snapped)\b",
    r"\bi\s+owe\s+you\s+an?\s+apolog",
    r"\bi\s+need\s+to\s+(do|be|work\s+on|try)\s+(better|harder|more)\b",
    r"\bthere.?s\s+no\s+excuse\s+for\s+(what\s+i|my|how\s+i)\b",
    r"\bi\s+let\s+you\s+down\b",
    r"\byou\s+deserved?\s+better\s+(from\s+me|than\s+that|than\s+what\s+i)\b",
]


# ==============================================================================
# SECTION 6: REPAIR ATTEMPT (Gottman — Repair Attempts)
# ==============================================================================

REPAIR_ATTEMPT_PATTERNS = [
    r"\bcan\s+we\s+(start\s+over|try\s+again|talk\s+about\s+this\s+calmly|reset)\b",
    r"\bi\s+don.?t\s+want\s+to\s+(fight|argue|lose\s+you|hurt\s+you)\b",
    r"\blet.?s\s+(take\s+a\s+)?breather?\b",
    r"\bi\s+love\s+you\s+(even\s+when|no\s+matter|and\s+i.?m\s+sorry|and\s+i\s+want\s+to\s+fix)\b",
    r"\bwe.?re\s+on\s+the\s+same\s+(team|side)\b",
    r"\bcan\s+i\s+(hug\s+you|hold\s+you|hold\s+your\s+hand)\b",
    r"\bi\s+miss\s+us\b",
    r"\blet.?s\s+not\s+go\s+to\s+(bed|sleep)\s+(mad|angry|upset)\b",
    r"\bi.?m\s+sorry,?\s+(can|let|please)\b",
    r"\bhow\s+can\s+(i|we)\s+(fix|make\s+(this|it)\s+(right|better))\b",
]


# ==============================================================================
# SECTION 7: ACTIVE LISTENING (Rogers — Empathic Listening)
# ==============================================================================

ACTIVE_LISTENING_PATTERNS = [
    r"\btell\s+me\s+more\s+(about)?\b",
    r"\bi.?m\s+listening\b",
    r"\bgo\s+on,?\s+i.?m\s+(here|all\s+ears)\b",
    r"\bwhat\s+(do\s+you\s+need|can\s+i\s+do|would\s+help|happened\s+next)\b",
    r"\bhow\s+(are|did|do)\s+you\s+(feel|feeling)\s*(about|after|now|today)?\b",
    r"\byou\s+were\s+saying\b",
    r"\bi\s+want\s+to\s+understand\b",
    r"\bhelp\s+me\s+understand\b",
    r"\bso\s+what\s+you.?re\s+saying\s+is\b",
]


# ==============================================================================
# SECTION 8: EMOTIONAL SUPPORT (Johnson, EFT — Engagement)
# ==============================================================================

EMOTIONAL_SUPPORT_PATTERNS = [
    r"\bi.?m\s+(right\s+)?here\s+for\s+you\b",
    r"\byou.?re\s+not\s+alone\s+in\s+this\b",
    r"\bwe.?ll\s+(get\s+through(\s+(this|it))?|figure\s+(this|it)\s+out|handle\s+this)\s+together\b",
    r"\bi.?ve\s+got\s+(you|your\s+back)\b",
    r"\byou\s+can\s+(always\s+)?(lean\s+on|count\s+on|depend\s+on|talk\s+to|come\s+to)\s+me\b",
    r"\bi\s+will\s+(always\s+)?(be\s+here|support\s+you|stand\s+by\s+you|have\s+your\s+back)\b",
    r"\bwhatever\s+(you\s+need|happens),?\s+i.?m\s+here\b",
    r"\bi.?m\s+not\s+going\s+anywhere\b",
    r"\byou\s+don.?t\s+have\s+to\s+(go\s+through|do|face)\s+(this|it)\s+alone\b",
]


# ==============================================================================
# SECTION 9: AFFIRMATION (Chapman — Words of Affirmation)
# ==============================================================================

AFFIRMATION_PATTERNS = [
    r"\byou.?re\s+(an?\s+)?(amazing|wonderful|incredible|beautiful|kind|smart|talented|brave|strong|resilient)(\s+(person|human|partner|friend|parent|soul))?\b",
    r"\bi.?m\s+(so\s+)?proud\s+to\s+be\s+with\s+you\b",
    r"\byou\s+make\s+me\s+(a\s+)?(better|want\s+to\s+be\s+better|so\s+happy)\b",
    r"\byou\s+are\s+(enough|worthy|loved|important|valued)\b",
    r"\byou\s+deserve\s+(good\s+things|happiness|love|the\s+best|to\s+be\s+happy)\b",
    r"\bi\s+admire\s+(you|your|how|the\s+way)\b",
    r"\byou\s+have\s+a\s+(good|kind|beautiful|generous|big)\s+heart\b",
]


# ==============================================================================
# SECTION 10: COMPROMISE (Gottman — Accepting Influence)
# ==============================================================================

COMPROMISE_PATTERNS = [
    r"\blet.?s\s+find\s+a\s+(middle\s+ground|compromise|solution|way)\b",
    r"\bwhat\s+if\s+we\s+(both|each|try|meet\s+in\s+the\s+middle)\b",
    r"\bi.?m\s+willing\s+to\s+(try|compromise|meet\s+you|work\s+on|change|adjust)\b",
    r"\bwe\s+can\s+(work\s+this\s+out|figure\s+this\s+out|find\s+a\s+way)\b",
    r"\bhow\s+about\s+we\s+(try|do|both|take\s+turns)\b",
    r"\bi\s+hear\s+your\s+(point|side|concern|perspective)\b",
    r"\byou\s+make\s+a\s+(good|fair|valid)\s+point\b",
    r"\blet.?s\s+(meet|work)\s+(halfway|together\s+on\s+this)\b",
    r"\bi\s+respect\s+(your|that)\s+(opinion|decision|point|view|perspective|boundary|choice)\b",
]


# ==============================================================================
# SECTION 11: BOUNDARY RESPECT (Healthy Autonomy)
# ==============================================================================

BOUNDARY_RESPECT_PATTERNS = [
    r"\btake\s+(your|all\s+the|as\s+much)\s+time(\s+as\s+you\s+need)?\b",
    r"\bwhenever\s+you.?re\s+ready\b",
    r"\bno\s+pressure\b",
    r"\bi\s+respect\s+your\s+(space|decision|choice|boundaries|need|feelings|privacy)\b",
    r"\bit.?s\s+(totally\s+|completely\s+)?(okay|ok|fine|your\s+(call|choice|decision))\s+(if\s+you|to\s+(say\s+no|not\s+want|need\s+space))?\b",
    r"\bi\s+understand\s+if\s+you\s+(need|don.?t\s+want|can.?t|aren.?t\s+ready)\b",
    r"\byou\s+don.?t\s+have\s+to\s+(explain|justify|decide\s+now|feel\s+bad)\b",
    r"\bi.?ll\s+(be\s+here\s+)?when(ever)?\s+you.?re\s+ready\b",
]


# ==============================================================================
# SECTION 12: REASSURANCE
# ==============================================================================

REASSURANCE_PATTERNS = [
    r"\bi\s+love\s+you\b",
    r"\bnothing\s+will\s+change\s+how\s+i\s+feel\s+about\s+you\b",
    r"\bwe.?re\s+(going\s+to\s+be\s+)?ok(ay)?\b",
    r"\bi.?m\s+not\s+(going\s+anywhere|leaving|giving\s+up)\b",
    r"\bthis\s+doesn.?t\s+change\s+(anything|how\s+i\s+feel|us)\b",
    r"\byou\s+can\s+trust\s+me\b",
    r"\bi.?ll\s+always\s+(love|choose|pick|want)\s+you\b",
    r"\bwe.?ll\s+get\s+through\s+this\b",
]


# ==============================================================================
# SECTION 13: GRATITUDE (Positive Reciprocity)
# ==============================================================================

GRATITUDE_PATTERNS = [
    r"\bthank\s+you\b",
    r"\bthanks\s+(so\s+much|a\s+lot|for\s+everything|for\s+being|babe|love)\b",
    r"\bi\s+can.?t\s+thank\s+you\s+enough\b",
    r"\byou.?re\s+the\s+best\b",
    r"\b(that|this)\s+means\s+(so\s+much|a\s+lot|the\s+world|everything)\s+to\s+me\b",
    r"\bi\s+really\s+needed\s+(that|this|to\s+hear\s+that)\b",
]


# ==============================================================================
# SECTION 14: VULNERABILITY (Brown — Authentic Connection)
# ==============================================================================

VULNERABILITY_PATTERNS = [
    r"\bi.?m\s+(scared|afraid|worried|anxious|nervous)\s+(that|about|of|to)\b",
    r"\bi\s+need\s+(you|your\s+help|to\s+talk|to\s+be\s+honest)\b",
    r"\bi\s+have\s+to\s+(be\s+honest|tell\s+you\s+something|admit\s+something)\b",
    r"\bthis\s+is\s+(hard|difficult|scary)\s+(for\s+me\s+)?(to\s+say|to\s+admit|to\s+talk\s+about)\b",
    r"\bi\s+feel\s+(insecure|vulnerable|exposed|scared)\b",
    r"\bi.?m\s+opening\s+up\s+(because|to\s+you)\b",
    r"\bi\s+trust\s+you\s+(with\s+this|enough\s+to|to)\b",
    r"\bcan\s+i\s+be\s+honest\s+with\s+you\b",
]


# ==============================================================================
# SECTION 15: UNIFIED SUPPORTIVE DETECTION ENGINE
# ==============================================================================

def detect_supportive_patterns(
    body: str,
    direction: str,
    msg_idx: int = -1,
    all_msgs: Optional[list] = None,
) -> List[SupportiveMatch]:
    """
    Detect positive/supportive communication patterns in a message.

    Mirrors the signature of detect_patterns() from patterns.py so both
    can be called identically. Returns supportive matches that indicate
    healthy communication behaviors.

    Args:
        body: The message text to analyze.
        direction: 'sent' or 'received'.
        msg_idx: Index of this message in all_msgs (reserved for future use).
        all_msgs: Full conversation list (reserved for future use).

    Returns:
        List of (supportive_category, matched_text, full_message) tuples.
    """
    if not body:
        return []

    lower = body.lower().strip()
    results: List[SupportiveMatch] = []

    def run(patterns, category):
        for p in patterns:
            m = re.search(p, lower)
            if m:
                results.append((category, m.group(), body))

    run(VALIDATION_PATTERNS, 'validation')
    run(EMPATHY_PATTERNS, 'empathy')
    run(APPRECIATION_PATTERNS, 'appreciation')
    run(ENCOURAGEMENT_PATTERNS, 'encouragement')
    run(ACCOUNTABILITY_PATTERNS, 'accountability')
    run(REPAIR_ATTEMPT_PATTERNS, 'repair_attempt')
    run(ACTIVE_LISTENING_PATTERNS, 'active_listening')
    run(EMOTIONAL_SUPPORT_PATTERNS, 'emotional_support')
    run(AFFIRMATION_PATTERNS, 'affirmation')
    run(COMPROMISE_PATTERNS, 'compromise')
    run(BOUNDARY_RESPECT_PATTERNS, 'boundary_respect')
    run(REASSURANCE_PATTERNS, 'reassurance')
    run(GRATITUDE_PATTERNS, 'gratitude')
    run(VULNERABILITY_PATTERNS, 'vulnerability')

    return results


# ==============================================================================
# SECTION 16: METADATA
# ==============================================================================

SUPPORTIVE_LABELS: Dict[str, str] = {
    'validation':       '✅ Validation',
    'empathy':          '💛 Empathy',
    'appreciation':     '🌻 Appreciation',
    'encouragement':    '💪 Encouragement',
    'accountability':   '🤝 Accountability',
    'repair_attempt':   '🔧 Repair Attempt',
    'active_listening': '👂 Active Listening',
    'emotional_support': '🫂 Emotional Support',
    'affirmation':      '⭐ Affirmation',
    'compromise':       '⚖️ Compromise',
    'boundary_respect': '🏳️ Boundary Respect',
    'reassurance':      '🛡️ Reassurance',
    'gratitude':        '🙏 Gratitude',
    'vulnerability':    '💎 Vulnerability',
}

SUPPORTIVE_DESCRIPTIONS: Dict[str, str] = {
    'validation':       'Acknowledging the other person\'s feelings and experiences as valid. (Gottman, 1999)',
    'empathy':          'Showing emotional understanding and compassion. (Johnson, 2008)',
    'appreciation':     'Expressing gratitude and recognizing the other person\'s value. (Gottman, 1999)',
    'encouragement':    'Supporting growth, effort, and resilience. (Chapman, 1992)',
    'accountability':   'Taking genuine responsibility for one\'s own actions. (Rosenberg, 2003)',
    'repair_attempt':   'Actively trying to de-escalate and reconnect during conflict. (Gottman, 1999)',
    'active_listening': 'Demonstrating attentive, engaged listening. (Rogers, 1961)',
    'emotional_support': 'Being present and available during emotional difficulty. (Johnson, 2008)',
    'affirmation':      'Affirming the other person\'s character and worth. (Chapman, 1992)',
    'compromise':       'Seeking mutually acceptable solutions and accepting influence. (Gottman, 1999)',
    'boundary_respect': 'Respecting the other person\'s autonomy, space, and choices.',
    'reassurance':      'Providing comfort and security about the relationship\'s stability.',
    'gratitude':        'Expressing thankfulness and positive reciprocity. (Algoe, 2012)',
    'vulnerability':    'Sharing authentic feelings openly, building trust. (Brown, 2012)',
}

# Supportive value ranking (higher = more impactful for relationship health).
#
# Rationale — derived from clinical research, not empirically validated on
# text corpora. Values reflect each behavior's significance in relationship
# stability literature:
#   - Empathy & accountability (10): Core predictors of repair and trust
#     (Gottman 1999, Johnson 2008, Rosenberg 2003).
#   - Repair attempts & vulnerability (9): Strongest predictors that a
#     relationship can survive conflict (Gottman 1999, Brown 2012).
#   - Validation & emotional support (8): Foundation of secure attachment
#     (Johnson 2008, Rogers 1961).
#   - Appreciation / affirmation / encouragement (7): Fondness & admiration
#     system (Gottman 1999, Chapman 1992).
#   - Compromise / active listening / boundary respect (6): Healthy
#     communication skills (Rosenberg 2003, Rogers 1961).
#   - Reassurance & gratitude (5): Important but more situational.
#
# NOTE: These weights have not been empirically validated through
# quantitative analysis of text-based communication datasets. Future work
# could refine them using annotated relationship outcome data.
SUPPORTIVE_VALUE: Dict[str, int] = {
    'empathy':          10,
    'accountability':   10,
    'repair_attempt':   9,
    'vulnerability':    9,
    'validation':       8,
    'emotional_support': 8,
    'appreciation':     7,
    'affirmation':      7,
    'encouragement':    7,
    'compromise':       6,
    'active_listening': 6,
    'boundary_respect': 6,
    'reassurance':      5,
    'gratitude':        5,
}
