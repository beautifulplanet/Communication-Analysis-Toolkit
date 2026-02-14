"""
================================================================================
Communication Analysis Toolkit — Pattern Detection Library
================================================================================

Clinical-grade behavioral pattern detection for text-based communication
analysis. Patterns are sourced from peer-reviewed psychology and communication
research:

SOURCES & REFERENCES:
  1. DARVO — Freyd, J.J. (1997). "Violations of power, adaptive blindness,
     and betrayal trauma theory." Feminism & Psychology, 7(1), 22-32.
  2. Gottman's Four Horsemen — Gottman, J.M. & Silver, N. (1999).
     "The Seven Principles for Making Marriage Work." Harmony Books.
  3. Duluth Model — Domestic Abuse Intervention Programs (1981).
     Power and Control Wheel. Duluth, MN.
  4. Coercive Control — Stark, E. (2007). "Coercive Control: How Men
     Entrap Women in Personal Life." Oxford University Press.
  5. Gaslighting — Stern, R. (2007). "The Gaslight Effect." Harmony Books.
  6. Narcissistic Abuse — Arabi, S. (2017). "Becoming the Narcissist's
     Nightmare." SCW Archer Publishing.
  7. Bancroft, L. (2002). "Why Does He Do That?: Inside the Minds of
     Angry and Controlling Men." Berkley Books.
  8. DSM-5 — APA (2013). Diagnostic and Statistical Manual of Mental
     Disorders, 5th Edition. Personality disorder behavioral criteria.
  9. RAINN — Rape, Abuse & Incest National Network. Emotional abuse
     indicators. https://www.rainn.org
  10. National DV Hotline — Signs of emotional abuse.
      https://www.thehotline.org

SEVERITY LEVELS:
  severe   — Personal attacks, weaponizing trauma, credible threats
  moderate — Directed profanity, insults aimed at the person, belittling
  mild     — Dismissive language, contextual profanity, passive aggression

PATTERN CATEGORIES:
  Core DARVO:
    deny, attack, reverse_victim

  Extended Manipulation:
    gaslighting, guilt_trip, deflection, minimizing, love_bombing,
    future_faking, triangulation, silent_treatment_threat

  Coercive Control (Stark, Duluth Model):
    control, isolation, financial_control, surveillance,
    weaponize_family, weaponize_health

  Gottman's Four Horsemen:
    criticism, contempt, defensiveness, stonewalling

  Interrogation & Pressure:
    looping, ultimatum, demand_for_compliance

  Deception:
    lying_indicator, trickle_truth, prank_test

  Emotional Exploitation:
    emotional_blackmail, catastrophizing, victim_narrative,
    selective_memory, double_bind

================================================================================
"""

import re
from typing import Any, Optional

# Type alias: (pattern_category, matched_text, full_message)
PatternMatch = tuple[str, str, str]


# ==============================================================================
# SECTION 1: HURTFUL LANGUAGE DETECTION (Context-Aware)
# ==============================================================================

# ── SEVERE: Personal attacks, weaponizing trauma, credible threats ──
SEVERE_PATTERNS: list[tuple[str, str]] = [
    # Weaponizing deceased family members
    (
        r"\bdead\s+(sissy|sister|brother|mom|dad|mother|father|baby|child)\b",
        "weaponizing deceased family",
    ),
    (r"\b(at\s+least\s+)?my\s+\w+\s+isn.?t\s+dead\b", "weaponizing death"),
    # Weaponizing health conditions
    (r"\bhelpless\s+(little\s+)?baby\b", "calling helpless baby"),
    (r"\byou.?re\s+a\s+baby\b", "calling a baby"),
    (r"\bwon.?t\s+stop\s+drinking\b", "weaponizing addiction"),
    (r"\bleave\s+you\s+in\s+the\s+hospital\b", "hospital abandonment threat"),
    (r"\bnever\s+see\w*\s+you\s+again\b", "permanent abandonment threat"),
    (
        r"\b(seizure|cancer|tumor|disease|disorder|illness)\b.*\byour\s+fault\b",
        "blaming for illness",
    ),
    # Direct threats
    (r"\bi.?ll\s+(kill|hurt|destroy|ruin)\s+(you|your)\b", "direct threat"),
    (r"\byou.?ll\s+(regret|pay\s+for|be\s+sorry)\b", "threat of retaliation"),
    (r"\bi\s+will\s+make\s+your\s+life\b", "threat to quality of life"),
    (r"\bno\s+one\s+will\s+(ever\s+)?(love|want|care\s+about)\s+you\b", "unlovability attack"),
    (r"\byou\s+deserve\s+to\s+(suffer|be\s+alone|die|hurt)\b", "wish of harm"),
    # Character assassination
    (r"\byou\s+don.?t\s+care\s+about\s+(me|anyone|anything)\b", "accusation of not caring"),
    (r"\byou\s+fucked\s+up\b", "blame statement"),
    (r"\bi\s+don.?t\s+care\b.*\bbecause\b", "weaponized indifference"),
    (r"\bkeep\s+bringing\s+it\s+up\b.*\bover\s+and\s+over\b", "stated looping intent"),
    (r"\byou.?re\s+(worthless|nothing|garbage|trash|a\s+waste)\b", "dehumanization"),
    (r"\bnobody\s+(likes|loves|wants|cares\s+about)\s+you\b", "social isolation attack"),
]

# ── MODERATE: Directed profanity and insults aimed at the person ──
MODERATE_DIRECTED: list[tuple[str, Optional[str]]] = [
    # "you [are] [insult]" patterns
    (
        r"\byou.?re\s+(so\s+)?(stupid|dumb|pathetic|useless|worthless|selfish|lazy|immature|childish|incompetent|ignorant|delusional|disgusting)\b",
        None,
    ),
    (r"\byou\s+(stupid|dumb|pathetic|useless|worthless|selfish)\b", None),
    # Direct personal profanity
    (r"\bfuck\s+you\b", "fuck you"),
    (r"\bscrew\s+you\b", "screw you"),
    (r"\bgo\s+to\s+hell\b", "go to hell"),
    (r"\beat\s+shit\b", "eat shit"),
    # Name-calling
    (
        r"\byou.?re\s+(an?\s+)?(idiot|moron|loser|narcissist|psycho|psychopath|sociopath|liar|bitch|asshole|piece\s+of\s+shit|cunt|bastard|whore|slut)\b",
        None,
    ),
    (r"\byou\s+(piece\s+of|sack\s+of)\b", None),
    # Directed hostility
    (r"\bshut\s+(the\s+fuck\s+)?up\b", "shut up"),
    (r"\bhate\s+you\b", "hate you"),
    (r"\bcan.?t\s+stand\s+you\b", "can't stand you"),
    (r"\bsick\s+of\s+you\b", "sick of you"),
    (r"\bdisgusted\s+by\s+you\b", "disgusted by you"),
    (r"\bi\s+wish\s+i\s+never\s+met\s+you\b", "wish never met"),
]

# ── MILD: Dismissive, contextual profanity in argument context ──
MILD_PROFANITY_WORDS = [
    "fuck",
    "fucking",
    "fucked",
    "shit",
    "shitty",
    "bullshit",
    "damn",
    "dammit",
    "crap",
    "ass",
    "hell",
]

MILD_DISMISSIVE: list[tuple[str, str]] = [
    (r"\bi\s+don.?t\s+care\b", "don't care"),
    (r"\bleave\s+me\s+alone\b", "leave me alone"),
    (r"\bget\s+lost\b", "get lost"),
    (r"\bgo\s+away\b", "go away"),
    (r"\bwhatever\b", "whatever"),
    (r"\bi\s+don.?t\s+have\s+time\s+for\s+this\b", "don't have time"),
    (r"\btalk\s+to\s+the\s+hand\b", "talk to the hand"),
    (r"\bi\s+don.?t\s+want\s+to\s+(hear|talk|discuss)\b", "don't want to discuss"),
]


def is_directed_hurtful(body: str, direction: str) -> tuple[bool, list[str], Optional[str]]:
    """
    Detect hurtful language directed AT a person, not casual usage.

    Returns:
        (is_hurtful, matched_words, severity)

    Severity:
        'severe'   — personal attacks, weaponizing trauma, threats
        'moderate' — directed profanity, insults aimed at the person
        'mild'     — dismissive language, casual profanity in argument context
        None       — benign usage
    """
    if not body:
        return False, [], None

    lower = body.lower().strip()
    found_words = []
    severity = None

    # ── SEVERE ──
    for sev_pattern, sev_label in SEVERE_PATTERNS:
        if re.search(sev_pattern, lower):
            found_words.append(sev_label)
            severity = "severe"

    # ── MODERATE ──
    for mod_pattern, mod_label in MODERATE_DIRECTED:
        if re.search(mod_pattern, lower):
            m = re.search(mod_pattern, lower)
            match_text = mod_label or (m.group() if m else "unknown")
            if match_text not in found_words:
                found_words.append(match_text)
            if severity != "severe":
                severity = "moderate"

    # ── MILD: Profanity in argument context (directed at "you") ──
    for word in MILD_PROFANITY_WORDS:
        if re.search(r"\b" + word + r"\b", lower):
            sentences = re.split(r"[.!?]+", lower)
            for sent in sentences:
                if word in sent and ("you" in sent or "your" in sent):
                    if word not in found_words:
                        found_words.append(word)
                    if severity is None:
                        severity = "mild"

    # ── MILD: Dismissive patterns ──
    for mild_pattern, mild_label in MILD_DISMISSIVE:
        if re.search(mild_pattern, lower):
            if mild_label not in found_words:
                found_words.append(mild_label)
            if severity is None:
                severity = "mild"

    if found_words:
        return True, found_words, severity
    return False, [], None


# ==============================================================================
# SECTION 2: DARVO DETECTION (Freyd, 1997)
# ==============================================================================

# Deny — Denying something they clearly did or said
DENY_PATTERNS = [
    r"i\s+never\s+said\s+that",
    r"i\s+didn.?t\s+(say|do|mean)\s+that",
    r"that.?s\s+not\s+(true|what\s+(happened|i\s+said))",
    r"you.?re\s+(making\s+that\s+up|lying|imagining)",
    r"that\s+didn.?t\s+happen",
    r"i\s+don.?t\s+remember\s+(saying|doing)",
    r"i\s+never\s+did\s+(that|anything)",
    r"prove\s+it",
    r"where.?s\s+(the\s+)?(proof|evidence)",
    r"you\s+(have|got)\s+no\s+proof",
]

# Attack — Turning it around to attack the other person
ATTACK_PATTERNS = [
    (
        r"you\s+always\s+\w+",
        lambda m: any(
            w in m.group()
            for w in [
                "ruin",
                "mess",
                "blame",
                "complain",
                "make",
                "start",
                "do this",
                "overreact",
                "twist",
                "lie",
                "destroy",
                "sabotage",
                "cause",
            ]
        ),
    ),
    (
        r"you\s+never\s+\w+",
        lambda m: any(
            w in m.group()
            for w in [
                "listen",
                "care",
                "help",
                "try",
                "change",
                "do anything",
                "learn",
                "understand",
                "apologize",
                "admit",
            ]
        ),
    ),
    (r"your\s+fault", None),
    (r"you.?re\s+the\s+(one|problem|reason)", None),
    (r"what\s+about\s+(when\s+)?you", None),
    (r"you\s+can.?t\s+(even|just)", None),
    (r"look\s+at\s+yourself", None),
    (r"you.?re\s+no\s+better", None),
    (r"you\s+do\s+(the\s+)?(same|it\s+too|worse)", None),
]

# Reverse Victim and Offender
REVERSE_VICTIM_PATTERNS = [
    r"you\s+(hurt|are\s+hurting)\s+me",
    r"you\s+made\s+me\s+(feel|do|cry|upset|act\s+this\s+way)",
    r"because\s+of\s+you",
    r"you\s+did\s+this\s+to\s+me",
    r"i.?m\s+(the\s+)?(real\s+)?victim",
    r"you\s+don.?t\s+care\s+about\s+me",
    r"you.?re\s+(abusing|manipulating|gaslighting|bullying)\s+me",
    r"i.?m\s+sad\s+because\s+of\s+you",
    r"you.?re\s+the\s+(abuser|manipulator|bully|toxic\s+one)",
    r"i.?m\s+the\s+one\s+who.?s\s+(suffering|hurting|in\s+pain)",
    r"look\s+what\s+you.?ve\s+done\s+to\s+me",
    r"you\s+drove\s+me\s+to\s+(this|it|drink|cry)",
]


# ==============================================================================
# SECTION 3: GASLIGHTING (Stern, 2007)
# ==============================================================================

GASLIGHTING_PATTERNS = [
    # Reality denial
    r"that\s+never\s+happened",
    r"that\s+didn.?t\s+happen",
    r"you.?re\s+(imagining|making)\s+(things|that|it)\s+up",
    r"you.?re\s+remembering\s+(it\s+)?wrong",
    r"that.?s\s+not\s+what\s+(happened|i\s+said|i\s+meant)",
    # Sanity questioning
    r"you.?re\s+(crazy|insane|delusional|paranoid|losing\s+it|losing\s+your\s+mind|unhinged|unstable|mental|nuts)",
    r"you\s+(seriously\s+)?need\s+(help|therapy|medication|a\s+doctor|professional\s+help)\s+(because|you.?re|,\s+you)",  # only when used as attack, not genuine suggestion
    r"you\s+sound\s+crazy",
    r"you.?re\s+the\s+only\s+one\s+who\s+thinks\s+that",
    r"something\s+is\s+(wrong|off)\s+with\s+you",
    r"are\s+you\s+sure\s+about\s+that\s*\?",  # patronizing questioning (not "are you ok")
    # Sensitivity shaming
    r"you.?re\s+too\s+sensitive",
    r"you.?re\s+(overreacting|being\s+dramatic|being\s+emotional|blowing\s+it\s+out)",
    r"stop\s+being\s+(so\s+)?(dramatic|sensitive|emotional|crazy|hysterical)",
    r"you\s+always\s+twist\s+(things|everything|my\s+words)",
    r"you\s+took\s+it\s+(the\s+)?wrong\s+way",
    # Joke deflection
    r"i\s+was\s+just\s+joking",
    r"can.?t\s+you\s+take\s+a\s+joke",
    r"i\s+didn.?t\s+mean\s+it\s+like\s+that",
    r"you\s+can.?t\s+take\s+a\s+(joke|compliment)",
    r"lighten\s+up",
    r"relax,?\s+it\s+was\s+(just\s+)?a\s+joke",
    # Social consensus weaponizing
    r"no\s+one\s+(else\s+)?(thinks|would\s+think|agrees\s+with\s+you)",
    r"everyone\s+(thinks|knows|says|agrees)\s+(you.?re|you\s+are|that\s+you)",
    r"ask\s+anyone",
    r"nobody\s+else\s+(has|would\s+have)\s+(a\s+)?problem\s+with\s+(this|that|it|me)",
    r"all\s+my\s+(friends|family)\s+(think|say)\s+(you.?re|that\s+you)",
]


# ==============================================================================
# SECTION 4: GOTTMAN'S FOUR HORSEMEN (Gottman & Silver, 1999)
# ==============================================================================

# Criticism — Attacking character rather than addressing behavior
CRITICISM_PATTERNS = [
    r"you\s+always\s+(do|are|make|ruin|mess|forget|ignore)",
    r"you\s+never\s+(do|are|help|listen|remember|learn|try|think)",
    r"what.?s\s+wrong\s+with\s+you",
    r"what\s+kind\s+of\s+(person|man|woman)\s+(are\s+you|does\s+that)",
    r"you.?re\s+just\s+like\s+your\s+(mom|dad|mother|father|ex)",
    r"you\s+can.?t\s+do\s+anything\s+right",
    r"you.?re\s+(impossible|hopeless|incapable|incompetent)",
    r"you\s+always\s+have\s+to\s+(be\s+right|have\s+the\s+last\s+word|argue|complain|ruin)",
]

# Contempt — Treating with disrespect, mockery, superiority
CONTEMPT_PATTERNS = [
    r"\b(duh|obviously|clearly)\b.*\byou",
    r"you.?re\s+so\s+(dumb|stupid|clueless|slow|dense|thick)",
    r"grow\s+up",
    r"act\s+your\s+age",
    r"what\s+are\s+you,?\s+\d+\s*(years?\s+old)?",  # "What are you, 5?"
    r"are\s+you\s+(a\s+)?(child|kid|baby|infant)",
    r"that.?s\s+the\s+dumbest\s+thing",
    r"you\b.*\bpathetic",
    r"\beye\s*roll\b",
    r"you.?re\s+not\s+(smart|good|capable|strong|mature)\s+enough",
    r"i\s+(can.?t\s+believe|am\s+embarrassed)\s+(i.?m|to\s+be)\s+with\s+you",
]

# Defensiveness — Deflecting responsibility, counter-blaming
DEFENSIVENESS_PATTERNS = [
    r"it.?s\s+not\s+my\s+fault",
    r"i\s+didn.?t\s+do\s+anything\s+(wrong|bad)",
    r"why\s+are\s+you\s+attacking\s+me",
    r"what\s+did\s+i\s+do(\s+wrong)?\s*\?",
    r"i\s+was\s+just\s+trying\s+to\s+(help|be\s+nice)",
    r"you\s+started\s+(it|this)",
    r"you.?re\s+the\s+one\s+who",
    r"if\s+you\s+hadn.?t\s+\w+",
    r"yeah\s+but\s+you",
    r"well\s+you\s+also",
    r"what\s+about\s+when\s+you",
]

# Stonewalling — Withdrawing, shutting down, refusal to engage
STONEWALLING_PATTERNS = [
    r"i.?m\s+(not\s+)?(going\s+to\s+)?(talk|discuss|engage|respond|answer|listen)\s+(about|to)\s+this",
    r"this\s+conversation\s+is\s+over",
    r"i\s+have\s+nothing\s+(more\s+)?(to\s+say|else\s+to\s+say)",
    r"i.?m\s+done\s+talking",
    r"i\s+don.?t\s+want\s+to\s+(talk|hear|discuss)\s+(about\s+)?(this|it)",
    r"don.?t\s+talk\s+to\s+me",
    r"i.?m\s+not\s+listening",
    r"talk\s+to\s+the\s+wall",
]


# ==============================================================================
# SECTION 5: COERCIVE CONTROL (Stark, 2007; Duluth Model)
# ==============================================================================

# Control & Isolation
CONTROL_PATTERNS = [
    r"you\s+(can.?t|shouldn.?t|better\s+not|are\s+not\s+allowed\s+to)\s+(talk|see|hang\s+out|go|visit|meet|text|call)\s+(to|with)",
    r"who\s+(are|were)\s+you\s+(with|talking\s+to|texting|calling|seeing)",
    r"(show|let)\s+me\s+(see\s+)?your\s+(phone|messages|texts|email|social\s+media|dms)",
    r"why\s+(are|were)\s+you\s+talking\s+to\s+(her|him|them|that\s+person)",
    r"you\s+don.?t\s+need\s+(them|friends|anyone\s+else|to\s+go\s+out)",
    r"i.?m\s+the\s+only\s+one\s+who\s+(loves|cares|understands|knows)\s+you",
    r"(if\s+you|you\s+better).*(or\s+else|or\s+i.?ll|or\s+we.?re\s+done)",
    r"you\s+have\s+to\s+(choose|pick)\s+(me|between)",
    r"it.?s\s+(me\s+)?or\s+(them|her|him)",
    r"you\s+spend\s+too\s+much\s+time\s+with",
    r"you\s+don.?t\s+need\s+to\s+(go|be\s+there|do\s+that|see\s+them)",
    r"i\s+need\s+to\s+know\s+where\s+you\s+are",
    r"(send|share)\s+(me\s+)?your\s+location",
    r"who\s+was\s+that\s+on\s+the\s+phone",
    r"why\s+didn.?t\s+you\s+(answer|pick\s+up|respond|call\s+me\s+back)",
    r"you\s+need\s+(my\s+)?permission",
]

# Financial Control
FINANCIAL_CONTROL_PATTERNS = [
    r"i\s+pay\s+(for\s+)?everything",
    r"you\s+(can.?t|don.?t)\s+afford",
    r"my\s+money",
    r"you\s+owe\s+me",
    r"i.?ll\s+(cut|stop)\s+(you\s+off|paying|supporting|helping)",
    r"you.?re\s+a\s+(financial\s+)?burden",
    r"without\s+me\s+you.?d\s+(be\s+)?(homeless|broke|on\s+the\s+street|nothing)",
    r"i\s+(gave|spent|wasted)\s+(\$|\d+|money|so\s+much)\s+(on\s+you|for\s+you)",
]

# Weaponizing Family/Health
WEAPONIZE_FAMILY_PATTERNS = [
    r"(mom|mother|dad|father|parent|family).*(seizure|cancer|hospital|drinking|sick|ill|dying|broke|rib|dies?|dead|condition)",
    r"(seizure|cancer|hospital|drinking|sick|dying|illness|condition).*(mom|mother|dad|father|parent|family)",
    r"dead\s+(siss|sister|brother|sibling|baby|child|friend)",
    r"leave\s+you\s+in\s+the\s+hospital",
    r"your\s+(mom|dad|mother|father|parent)\s+(is|was)\s+(a|an)\s+\w+",
    r"(at\s+least\s+)?(my|i)\s+(mom|dad|mother|father|parent)\s+(isn.?t|doesn.?t|wouldn.?t|didn.?t)",
    r"you.?re\s+going\s+to\s+end\s+up\s+like\s+your\s+(mom|dad|mother|father)",
]


# ==============================================================================
# SECTION 6: EXTENDED MANIPULATION PATTERNS
# ==============================================================================

# Guilt Trip
GUILT_TRIP_PATTERNS = [
    r"after\s+everything\s+i.?(ve)?\s+(done|did|gave|sacrificed)",
    r"i\s+(gave|did|sacrificed)\s+(so\s+much|everything)",
    r"you.?d\s+be\s+nothing\s+without\s+me",
    r"you\s+owe\s+me",
    r"without\s+me\s+you",
    r"i\s+put\s+up\s+with\s+(so\s+much|everything|all\s+your)",
    r"do\s+you\s+know\s+how\s+much\s+i.?(ve)?\s+(done|sacrificed|given\s+up)",
    r"i\s+dropped\s+everything\s+for\s+you",
    r"i\s+gave\s+up\s+\w+\s+for\s+you",
    r"i\s+stayed\s+when\s+(no\s+one\s+else|anyone\s+else)\s+would.?ve\s+(left|given\s+up)",
]

# Deflection
DEFLECTION_PATTERNS = [
    r"that.?s\s+not\s+the\s+point",
    r"you.?re\s+changing\s+the\s+subject",
    r"we.?re\s+not\s+talking\s+about",
    r"stop\s+deflecting",
    r"the\s+(real\s+)?issue\s+is",
    r"what\s+about\s+when\s+you",
    r"remember\s+when\s+you",
    r"but\s+you\s+also\s+did",
    r"well\s+what\s+about",
    r"you.?re\s+avoiding\s+the\s+(question|issue|point)",
]

# Ultimatums & Threats
ULTIMATUM_PATTERNS = [
    r"(i.?m\s+)?(going\s+to\s+)?(leave|leaving)\s+(you|and\s+never)",
    r"(then\s+)?we.?re\s+(done|through|over|finished)",
    r"i.?m\s+(done|leaving|going\s+to\s+\w+\s+and\s+never)",
    r"never\s+see\w*\s+you\s+again",
    r"stop\s+texting\s+me",
    r"leave\s+me\s+alone",
    r"if\s+you\s+can.?t\s+do\s+that.*leave",
    r"if\s+you\s+(don.?t|can.?t|won.?t).*i.?m\s+(leaving|done|going|out)",
    r"this\s+is\s+your\s+last\s+chance",
    r"i.?m\s+giving\s+you\s+(one|a)\s+(more\s+)?(chance|try|shot)",
    r"you.?re\s+going\s+to\s+lose\s+me",
    r"i\s+won.?t\s+be\s+here\s+(forever|much\s+longer|when\s+you\s+come\s+back)",
]

# Looping / Interrogation (Bancroft, 2002)
LOOPING_PATTERNS = [
    r"(keep|going\s+to)\s+bring\w*\s+it\s+up",
    r"over\s+and\s+over(\s+and\s+over)?(\s+again)?",
    r"until\s+you\s+(can|do|tell|admit|say|acknowledge|apologize|confess)",
    r"i.?ll\s+keep\s+asking",
    r"we.?re\s+not\s+done\s+(talking|discussing)\s+(about\s+)?(this|it)",
    r"i\s+won.?t\s+(stop|let\s+this\s+go|drop\s+it)\s+until",
    r"answer\s+the\s+question",
    r"just\s+answer\s+me",
    r"why\s+(won.?t|can.?t)\s+you\s+just\s+(answer|tell|say|admit)",
]

# Lying Indicators
LYING_INDICATOR_PATTERNS = [
    r"i\s+(already|just)\s+told\s+you",
    r"i\s+never\s+said\s+(i\s+would|that|anything)",
    r"i\s+didn.?t\s+(say|do|promise|agree)\s+(that|to)",
    r"that.?s\s+not\s+what\s+i\s+(said|meant|did)",
    r"you.?re\s+putting\s+words\s+in\s+my\s+mouth",
    r"why\s+(do|would)\s+i\s+(lie|make\s+that\s+up)",
    r"i\s+swear\s+i\s+didn.?t",
    r"believe\s+what\s+you\s+want",
    r"think\s+whatever\s+you\s+want",
    r"(prove|show)\s+(it|me)",
    r"i\s+would\s+never\s+do\s+that",
]

# Minimizing (downplaying the other person's feelings)
MINIMIZING_PATTERNS = [
    r"it.?s\s+not\s+(that\s+)?(big\s+of\s+a|a\s+big)\s+deal",
    r"you.?re\s+(blowing|making)\s+(this|it)\s+(out\s+of\s+proportion|into\s+a\s+big\s+deal|bigger)",
    r"it\s+wasn.?t\s+(even\s+)?(that\s+)?bad",
    r"i\s+was\s+just\s+(playing|messing|kidding)",
    r"it\s+was\s+(just\s+)?a\s+(joke|prank)",
    r"get\s+over\s+it",
    r"let\s+it\s+go",
    r"why\s+are\s+you\s+still\s+(upset|mad|angry|bringing\s+this\s+up)",
    r"it\s+happened\s+(so\s+long|a\s+while|days|weeks|months)\s+ago",
    r"you.?re\s+still\s+(on|about)\s+(this|that)",
    r"move\s+on\s+already",
    r"you\s+need\s+to\s+(get\s+over|move\s+past|let\s+go\s+of)\s+(this|it|that)",
]

# Love Bombing (Arabi, 2017)
LOVE_BOMBING_PATTERNS = [
    r"you.?re\s+my\s+(everything|world|soulmate|other\s+half|reason\s+for\s+living)",
    r"i.?ve\s+never\s+(felt|loved|met)\s+(anyone|someone)\s+like\s+(you|this)",
    r"we.?re\s+(meant|destined)\s+to\s+be",
    r"i\s+can.?t\s+live\s+without\s+you",
    r"you\s+complete\s+me",
    r"no\s+one\s+(will\s+ever|could\s+ever)\s+(love|understand|know)\s+you\s+like\s+i\s+do",
    r"we\s+should\s+(move\s+in|get\s+married|have\s+kids)\s+already",  # premature commitment
    r"i\s+knew\s+(from|the\s+moment)\b.*\byou\s+were\s+the\s+one",
]

# Future Faking
FUTURE_FAKING_PATTERNS = [
    r"(when|once)\s+we\s+(move|get\s+married|have\s+kids|buy\s+a\s+house)",
    r"i\s+promise\s+i.?ll\s+(change|be\s+better|stop|never\s+do\s+it\s+again)",
    r"things\s+will\s+(be\s+)?different\s+(this\s+time|from\s+now\s+on|i\s+promise)",
    r"just\s+give\s+me\s+(one\s+more|another)\s+chance",
    r"i.?m\s+going\s+to\s+(change|be\s+better|work\s+on\s+it|go\s+to\s+therapy)",
    r"it\s+won.?t\s+happen\s+again",
    r"i\s+swear\s+on\s+my\b",
]

# Triangulation (introducing third parties)
TRIANGULATION_PATTERNS = [
    r"(my\s+)?(ex|friend|coworker|boss|mom|dad)\s+(thinks|said|agrees)\s+(you.?re|that\s+you|i\s+should|you\s+should)",
    r"even\s+(my|your)\s+(mom|dad|friend|sister|brother)\s+(thinks|said|agrees)",
    r"at\s+least\s+(he|she|they|my\s+ex)\s+(didn.?t|would|never|always)",
    r"(he|she|they)\s+(would\s+)?never\s+(treat|do\s+this\s+to|talk\s+to)\s+me\s+like\s+(this|that|you\s+do)",
    r"maybe\s+i\s+should\s+(go\s+back\s+to|be\s+with|call)\s+(my\s+)?ex",
    r"other\s+(guys|girls|people|men|women)\s+(would|don.?t|wouldn.?t)",
]

# Emotional Blackmail (Forward & Frazier, 1997)
EMOTIONAL_BLACKMAIL_PATTERNS = [
    r"if\s+you\s+(loved|cared\s+about|really\s+loved)\s+me.*you\s+(would|wouldn.?t)",
    r"if\s+you\s+leave\s+i.?ll\s+(kill\s+myself|hurt\s+myself|die|be\s+nothing)",
    r"you.?re\s+the\s+(reason|cause)\s+i\s+(feel|am)\s+(this\s+way|depressed|anxious|suicidal)",
    r"i\s+can.?t\s+(go\s+on|survive|live)\s+without\s+you",
    r"if\s+you\s+(really\s+)?(care|love)\s+(about\s+me|me).*prove\s+it",
    r"a\s+(real|good|loving)\s+(boyfriend|girlfriend|partner|husband|wife)\s+would",
]

# Silent Treatment Threat
SILENT_TREATMENT_PATTERNS = [
    r"i.?m\s+not\s+(going\s+to\s+)?(talk|speak|respond|answer|reply)\s+to\s+you",
    r"don.?t\s+(bother\s+)?(calling|texting|messaging|contacting)\s+me",
    r"i\s+need\s+(space|time\s+away\s+from\s+you|to\s+be\s+alone)",
    r"you.?ll\s+hear\s+from\s+me\s+when\s+i.?m\s+ready",
    r"i.?m\s+going\s+(radio\s+)?silent",
]

# Double Bind (Bateson, 1956)
DOUBLE_BIND_PATTERNS = [
    r"(damned|screwed)\s+if\s+you\s+do.*(damned|screwed)\s+if\s+you\s+don.?t",
    r"whatever\s+you\s+do\s+(is\s+)?(wrong|not\s+good\s+enough|a\s+problem)",
    r"if\s+you\s+\w+\s+i.?ll\s+be\s+(mad|upset|angry|hurt).*if\s+you\s+don.?t.*i.?ll\s+be\s+(mad|upset|angry|hurt)",
    r"you\s+can.?t\s+win",
    r"nothing\s+you\s+do\s+is\s+(ever\s+)?(right|enough|good\s+enough)",
]

# Prank/Test — Fake scenarios to test reactions
PRANK_TEST_PATTERNS = [
    r"(it\s+was|just)\s+(a\s+)?(prank|test|joke|experiment)",
    r"i\s+was\s+(just\s+)?(testing|checking|seeing)",
    r"i\s+wanted\s+to\s+see\s+(how|if|what)\s+you",
    r"you\s+said\s+you\s+would\s+(hit|hurt|leave)",
    r"you\s+threatened\s+(to|me)",
]

# Selective Memory / Trickle Truth
SELECTIVE_MEMORY_PATTERNS = [
    r"i\s+forgot\s+to\s+(mention|tell\s+you|say)",
    r"oh\s+i\s+didn.?t\s+think\s+(it\s+was|that\s+was)\s+(important|relevant|a\s+big\s+deal)",
    r"i\s+only\s+(told|said|did)\s+\w+\s+because",
    r"well\s+there.?s\s+(one\s+more|something\s+else|another)\s+thing",
    r"i\s+didn.?t\s+tell\s+you\s+(because|since)",
]

# Catastrophizing
CATASTROPHIZING_PATTERNS = [
    r"(everything|nothing)\s+(is\s+)?(ruined|terrible|awful|wrong|broken|falling\s+apart|a\s+disaster|messed\s+up)",
    r"(always|never)\s+(goes\s+wrong|fails|works\s+out|turns\s+out\s+bad)",
    r"the\s+world\s+is\s+(ending|against\s+me|falling\s+apart)",
    r"nothing\s+ever\s+(works|goes\s+right|changes)",
    r"(my|our)\s+life\s+is\s+(ruined|over|destroyed|a\s+disaster)",
    r"we.?re\s+(never\s+going\s+to|doomed|finished|hopeless)",
]

# Demand for Compliance
DEMAND_COMPLIANCE_PATTERNS = [
    r"you\s+(need|have)\s+to\s+(do|say|agree|apologize|admit|accept)\s+(what|that|this)",
    r"just\s+(do|say|agree|admit|accept)\s+(it|what\s+i)",
    r"say\s+(you.?re\s+)?sorry",
    r"admit\s+(it|what\s+you\s+did|you\s+were\s+wrong)",
    r"agree\s+with\s+me",
    r"take\s+(it\s+)?back",
    r"you\s+will\s+(say|do|agree|admit)\s+(it|this|that)",
]


# ==============================================================================
# SECTION 6B: CONTEXT FILTERS (reduce false positives)
# ==============================================================================
# These filters dramatically reduce false positives by recognizing when
# flagged language is actually benign (apologies, self-directed, jokes, etc.).
# Ported from the monthly report analysis pipeline's battle-tested functions.


def is_apology(body: str) -> bool:
    """Check if message is an apology/conciliatory, not an attack."""
    if not body:
        return False
    lower = body.lower()
    apology_markers = [
        r"\b(i.?m |im |i am )?(really |so |truly |very )?(sorry|apologize|apologise)\b",
        r"\bmy bad\b",
        r"\bmy fault\b",
        r"\bi was wrong\b",
        r"\bi shouldn.?t have\b",
        r"\bi should have\b",
        r"\bforgive me\b",
        r"\bplease.*chance\b",
        r"\bi.?ll (do |try |be )better\b",
        r"\bi (messed|screwed|fucked) up\b",
        r"\byou.?re right\b",
        r"\byou were right\b",
    ]
    return any(re.search(pat, lower) for pat in apology_markers)


def is_self_directed(body: str) -> bool:
    """Check if negativity is about self, not the other person."""
    if not body:
        return False
    lower = body.lower()
    self_patterns = [
        r"\bi.?m\s+(a |an |such a |the )?(shit|ass|idiot|stupid|terrible|worst|bad|awful|mess)",
        r"\bi\s+(suck|hate myself|messed up|screwed up|fucked up)\b",
        r"\bi\s+should\s+(shut up|stop|have)\b",
        r"\bmy fault\b",
        r"\bmy bad\b",
        r"\bi was wrong\b",
    ]
    return any(re.search(pat, lower) for pat in self_patterns)


def is_third_party_venting(body: str) -> bool:
    """Check if negativity is about work/family/outside situation, not partner."""
    if not body:
        return False
    lower = body.lower()
    third_party = [
        r"\b(my |the )?(worker|boss|client|customer|employee|coworker|colleague|manager|contractor|guy|tenant)\b",
        r"\b(this |that |the )?(job|work|company|business|office|site)\b.*\b(sucks?|terrible|awful|shit|fuck|annoying|ridiculous)\b",
        r"\b(my |the )?(car|truck|phone|computer|laptop)\b.*\b(broke|dead|fucked|shit)\b",
        r"\b(traffic|weather|subway|train|bus)\b.*\b(sucks?|awful|terrible|shit|fuck)\b",
    ]
    return any(re.search(pat, lower) for pat in third_party)


def is_de_escalation(body: str) -> bool:
    """Check if a message is attempting to de-escalate / calm things down."""
    if not body:
        return False
    lower = body.lower()
    de_esc = [
        r"\b(let.?s |can we |we should )(stop|calm|relax|chill|drop it|move on|not fight|not argue)\b",
        r"\b(please |just )?(calm down|stop fighting|stop arguing|stop this|enough)\b",
        r"\bcan we (just |please )?(talk|discuss) (calmly|nicely|like adults|normally)\b",
        r"\bi don.?t want to (fight|argue)\b",
        r"\blet.?s not (fight|argue|do this)\b",
        r"\bcan we (move on|move past|drop)\b",
        r"\bi.?m (trying to|not trying to)\s*(fight|argue|upset you|make you mad)\b",
        r"\bi need (a |some )?(space|break|minute|time)\b",
        r"\bplease stop\b",
        r"\blet.?s just\b.*\b(tomorrow|later|another time|sleep|rest)\b",
    ]
    return any(re.search(pat, lower) for pat in de_esc)


def is_expressing_hurt(body: str) -> bool:
    """
    Check if message is expressing hurt, disappointment, or emotional pain
    rather than attacking. 'sounds like you don't wanna see me' after
    being rejected is a normal human response, not hostility.
    """
    if not body:
        return False
    lower = body.lower()
    hurt_patterns = [
        r"\b(sounds like|feels like|seems like)\s+you\s+(don.?t|do not|doesn.?t)\s*(want|wanna|care|like|love|miss)",
        r"\byou\s+(don.?t|do not)\s+(want to|wanna)\s+(see|be with|talk to|hang out|spend time)",
        r"\byou\s+(don.?t|do not)\s+(want|wanna)\s+me\b",
        r"\byou\s+(don.?t|do not)\s+(miss|need|love)\s+me\b",
        r"\bi\s+(miss|love|need)\s+you\b",
        r"\bthis\s+(sucks|hurts|isn.?t fair|is hard)\b",
        r"\bi\s+(don.?t|do not)\s+know\s+what\s+to\s+(do|say)\b",
        r"\bwhat\s+(am|do)\s+i\s+supposed\s+to\b",
        r"\bi\s+(don.?t|do not)\s+want(a|\s+to)\s+(argue|fight|lose|bother|upset)\b",
        r"\bare\s+you\s+(dumping|breaking|leaving|done with)\b",
        r"\bplease\s+(don.?t|do not)\s+(dump|leave|break up|go)\b",
        r"\bi\s+hope\s+you.?(re|\s+are)\s+ok\b",
        r"\bidk\s+what\s+to\s+(say|do)\b",
    ]
    return any(re.search(pat, lower) for pat in hurt_patterns)


def is_joke_context(msg_idx: int, all_msgs: list[Any], window: int = 3) -> bool:
    """
    Check if a message is in a joking/playful context by looking at surrounding messages.
    Returns True if laughter/playful signals are nearby (2+ in window).
    """
    joke_signals = [
        r"(?:\b(?:lol|lmao|lmfao|haha+|rofl)\b|😂|🤣|😆|😹|💀)",
        r"^(?:lol|haha|lmao|😂)$",
        r"(?:\b(?:jk|just kidding|joking|kidding)\b)",
        r"(?:🤪|😜|😝|🤡|😏|😈|🙃)",
    ]
    start = max(0, msg_idx - window)
    end = min(len(all_msgs), msg_idx + window + 1)

    laugh_count = 0
    for i in range(start, end):
        body = (all_msgs[i].get("body", "") or "").lower()
        for pat in joke_signals:
            if re.search(pat, body):
                laugh_count += 1
                break

    return laugh_count >= 2


def is_banter(msg_idx: int, all_msgs: list[Any], window: int = 4) -> bool:
    """
    Check if messages around this index are playful banter (both sides laughing).
    Returns True if both people are engaged in light exchanges.
    """
    start = max(0, msg_idx - window)
    end = min(len(all_msgs), msg_idx + window + 1)
    banter_words = r"(?:\b(?:lol|lmao|haha+|omg|bruh|bro|dude)\b|😂|🤣|💀|😭|😆)"

    sent_laughing = False
    recv_laughing = False
    for i in range(start, end):
        m = all_msgs[i]
        body = (m.get("body", "") or "").lower()
        if re.search(banter_words, body):
            if m.get("direction") == "sent":
                sent_laughing = True
            else:
                recv_laughing = True

    return sent_laughing and recv_laughing


# ==============================================================================
# SECTION 7: UNIFIED DETECTION ENGINE
# ==============================================================================


def detect_patterns(
    body: str,
    direction: str,
    msg_idx: int = -1,
    all_msgs: Optional[list[Any]] = None,
) -> list[PatternMatch]:
    """
    Run all pattern detection categories against a message with optional
    context-aware filtering to reduce false positives.

    Args:
        body: The message text to analyze.
        direction: 'sent' or 'received' (relative to the user running the tool).
        msg_idx: Index of this message in all_msgs (enables joke/banter checks).
        all_msgs: Full conversation list (enables surrounding-context checks).

    Returns:
        List of (pattern_category, matched_text, full_message) tuples.
    """
    if not body:
        return []

    lower = body.lower().strip()
    results: list[PatternMatch] = []

    # --- Context filters (computed once per message) ---
    _apology = is_apology(body)
    _self = is_self_directed(body)
    _third = is_third_party_venting(body)
    _de_esc = is_de_escalation(body)
    _hurt = is_expressing_hurt(body)

    # Context checks that need conversation window
    _joke = False
    _banter_flag = False
    if msg_idx >= 0 and all_msgs:
        _joke = is_joke_context(msg_idx, all_msgs)
        _banter_flag = is_banter(msg_idx, all_msgs)

    # Categories where we skip mild matches when context is benign.
    # High-severity categories (control, gaslighting, weaponize_family,
    # emotional_blackmail, etc.) are NEVER skipped.
    MILD_SKIP_CATEGORIES = {
        "defensiveness",
        "stonewalling",
        "deflection",
        "minimizing",
        "catastrophizing",
        "demand_compliance",
        "criticism",
        "guilt_trip",
        "silent_treatment",
        "selective_memory",
    }

    def _skip_mild(category: str) -> bool:
        """Return True if this category should be suppressed for this message."""
        if category not in MILD_SKIP_CATEGORIES:
            return False
        return _apology or _self or _third or _de_esc or _hurt or _joke or _banter_flag

    # Helper: run a list of simple regex patterns
    def run_simple(patterns: list[str], category: str) -> None:
        if _skip_mild(category):
            return
        for p in patterns:
            m = re.search(p, lower)
            if m:
                results.append((category, m.group(), body))

    # Helper: run patterns with optional validators
    def run_validated(patterns: list[Any], category: str) -> None:
        if _skip_mild(category):
            return
        for item in patterns:
            if isinstance(item, tuple):
                p, validator = item
            else:
                p, validator = item, None
            m = re.search(p, lower)
            if m and (validator is None or validator(m)):
                results.append((category, m.group(), body))

    # ── Core DARVO ──
    run_simple(DENY_PATTERNS, "deny")
    run_validated(ATTACK_PATTERNS, "attack")
    run_simple(REVERSE_VICTIM_PATTERNS, "reverse_victim")

    # ── Gaslighting ──
    run_simple(GASLIGHTING_PATTERNS, "gaslighting")

    # ── Gottman's Four Horsemen ──
    run_simple(CRITICISM_PATTERNS, "criticism")
    run_simple(CONTEMPT_PATTERNS, "contempt")
    run_simple(DEFENSIVENESS_PATTERNS, "defensiveness")
    run_simple(STONEWALLING_PATTERNS, "stonewalling")

    # ── Coercive Control ──
    run_simple(CONTROL_PATTERNS, "control")
    run_simple(FINANCIAL_CONTROL_PATTERNS, "financial_control")
    run_simple(WEAPONIZE_FAMILY_PATTERNS, "weaponize_family")

    # ── Extended Manipulation ──
    run_simple(GUILT_TRIP_PATTERNS, "guilt_trip")
    run_simple(DEFLECTION_PATTERNS, "deflection")
    run_simple(ULTIMATUM_PATTERNS, "ultimatum")
    run_simple(LOOPING_PATTERNS, "looping")
    run_simple(LYING_INDICATOR_PATTERNS, "lying_indicator")
    run_simple(MINIMIZING_PATTERNS, "minimizing")
    run_simple(LOVE_BOMBING_PATTERNS, "love_bombing")
    run_simple(FUTURE_FAKING_PATTERNS, "future_faking")
    run_simple(TRIANGULATION_PATTERNS, "triangulation")
    run_simple(EMOTIONAL_BLACKMAIL_PATTERNS, "emotional_blackmail")
    run_simple(SILENT_TREATMENT_PATTERNS, "silent_treatment")
    run_simple(DOUBLE_BIND_PATTERNS, "double_bind")
    run_simple(PRANK_TEST_PATTERNS, "prank_test")
    run_simple(SELECTIVE_MEMORY_PATTERNS, "selective_memory")
    run_simple(CATASTROPHIZING_PATTERNS, "catastrophizing")
    run_simple(DEMAND_COMPLIANCE_PATTERNS, "demand_compliance")

    return results


# ==============================================================================
# SECTION 8: PATTERN METADATA (for reports and UI)
# ==============================================================================

PATTERN_LABELS: dict[str, str] = {
    # Core DARVO
    "deny": "🚫 Denial (DARVO)",
    "attack": "⚔️ Attack (DARVO)",
    "reverse_victim": "🔄 Reverse Victim & Offender (DARVO)",
    # Gaslighting
    "gaslighting": "🌀 Gaslighting",
    # Gottman's Four Horsemen
    "criticism": "🗡️ Criticism (Gottman)",
    "contempt": "😤 Contempt (Gottman)",
    "defensiveness": "🛡️ Defensiveness (Gottman)",
    "stonewalling": "🧱 Stonewalling (Gottman)",
    # Coercive Control
    "control": "🔒 Control & Isolation",
    "financial_control": "💰 Financial Control",
    "weaponize_family": "💀 Weaponizing Family/Health",
    # Extended Manipulation
    "guilt_trip": "😢 Guilt Trip",
    "deflection": "↩️ Deflection",
    "ultimatum": "⚡ Ultimatums & Threats",
    "looping": "🔁 Looping / Interrogation",
    "lying_indicator": "🤥 Lying Indicators",
    "minimizing": "📉 Minimizing",
    "love_bombing": "💣 Love Bombing",
    "future_faking": "🔮 Future Faking",
    "triangulation": "📐 Triangulation",
    "emotional_blackmail": "🖤 Emotional Blackmail",
    "silent_treatment": "🤐 Silent Treatment Threat",
    "double_bind": "♾️ Double Bind",
    "prank_test": "🎭 Prank / Testing Reactions",
    "selective_memory": "🧠 Selective Memory / Trickle Truth",
    "catastrophizing": "🌪️ Catastrophizing",
    "demand_compliance": "📋 Demand for Compliance",
}

PATTERN_DESCRIPTIONS: dict[str, str] = {
    "deny": "Denying something they clearly did or said. (Freyd, 1997)",
    "attack": "Turning it around to attack the other person. (Freyd, 1997)",
    "reverse_victim": "Making themselves the victim when they are the offender. (Freyd, 1997)",
    "gaslighting": "Making someone question their perception of reality. (Stern, 2007)",
    "criticism": "Attacking character rather than addressing specific behavior. (Gottman, 1999)",
    "contempt": "Treating with disrespect, mockery, superiority, or sarcasm. (Gottman, 1999)",
    "defensiveness": "Deflecting responsibility and counter-blaming. (Gottman, 1999)",
    "stonewalling": "Withdrawing, shutting down, or refusing to engage. (Gottman, 1999)",
    "control": "Controlling who the person sees, talks to, or where they go. (Stark, 2007)",
    "financial_control": "Using money or finances as a weapon or leverage. (Duluth Model)",
    "weaponize_family": "Using family illness, death, or trauma as leverage. (Bancroft, 2002)",
    "guilt_trip": "Inducing guilt to manipulate behavior or compliance.",
    "deflection": "Changing the subject or redirecting blame when confronted.",
    "ultimatum": "Threatening to leave, end things, or impose consequences.",
    "looping": "Repeating the same issue until they get the desired response. (Bancroft, 2002)",
    "lying_indicator": "Patterns consistent with deception, denial, or story-changing.",
    "minimizing": "Downplaying the other person's feelings or experiences.",
    "love_bombing": "Excessive affection/attention used to overwhelm boundaries. (Arabi, 2017)",
    "future_faking": "Making promises about the future with no intention to follow through.",
    "triangulation": "Introducing third parties to create jealousy or validate position.",
    "emotional_blackmail": "Using fear, obligation, or guilt to control. (Forward & Frazier, 1997)",
    "silent_treatment": "Weaponized withdrawal of communication as punishment.",
    "double_bind": "Creating a lose-lose situation where all choices are punished.",
    "prank_test": "Fabricating scenarios to test reactions or entrap.",
    "selective_memory": "Conveniently forgetting or revealing information incrementally.",
    "catastrophizing": "Exaggerating situations to create urgency or panic.",
    "demand_compliance": "Demanding agreement, apology, or submission without negotiation.",
}

# Severity ranking for pattern categories (higher = more concerning)
PATTERN_SEVERITY: dict[str, int] = {
    "weaponize_family": 10,
    "gaslighting": 9,
    "emotional_blackmail": 9,
    "control": 8,
    "financial_control": 8,
    "reverse_victim": 8,
    "double_bind": 7,
    "looping": 7,
    "ultimatum": 7,
    "triangulation": 6,
    "love_bombing": 6,
    "deny": 6,
    "attack": 6,
    "contempt": 6,
    "guilt_trip": 5,
    "lying_indicator": 5,
    "prank_test": 5,
    "criticism": 5,
    "future_faking": 5,
    "selective_memory": 4,
    "minimizing": 4,
    "deflection": 4,
    "demand_compliance": 4,
    "catastrophizing": 3,
    "defensiveness": 3,
    "stonewalling": 3,
    "silent_treatment": 3,
}
