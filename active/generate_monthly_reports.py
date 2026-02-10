"""
============================================================================
MONTHLY CONVERSATION BREAKDOWN — Detailed Analysis per Month
============================================================================
Creates per-month markdown files with:
  - Full daily message logs (grouped by conversation flow)
  - Daily summary: who initiated, tone, argument tracking
  - Weekly rollup with patterns
  - Argument initiation detection (who started it, how)
  - Subtle behavior pattern flagging
  - Verification data (msg counts, timestamps) for cross-checking
  - Missing context flags for manual review
  - Footnotes on behavioral dynamics

Each file is sized to fit in ChatGPT's context window (~50-80 pages max).
============================================================================
"""
import json
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# ──────────────────────────────────────────────────────────────────────────────
# SECURITY HELPERS
# ──────────────────────────────────────────────────────────────────────────────

_MD_ESCAPE_RE = re.compile(r'([\\`*_\{\}\[\]()#+\-.!|>~])')

def escape_md(text: str) -> str:
    """Escape markdown special characters in user-supplied text."""
    if not text:
        return text
    return _MD_ESCAPE_RE.sub(r'\\\1', text)

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — loaded from config.json, no hardcoded values
# ──────────────────────────────────────────────────────────────────────────────

import argparse

SIGNAL_DESKTOP_JSON = ""
SMS_XML = ""
CALLS_XML = ""
SIGNAL_DB = ""
OUTPUT_DIR = ""
CONTACT_PHONE = ""
PHONE_SUFFIX = ""
CONTACT_NAME = ""
USER_NAME = ""

# ──────────────────────────────────────────────────────────────────────────────
# BEHAVIOR / TONE DETECTION
# ──────────────────────────────────────────────────────────────────────────────

# Negative tone indicators — subtle ones that precede arguments
PASSIVE_AGGRESSIVE_PATTERNS = [
    (r'\bfine\b\.?$', 'passive_aggressive'),
    (r'\bwhatever\b', 'dismissive'),
    (r'\bok\b\.?$', 'curt_response'),  # standalone "ok" or "ok."
    (r'\bk\b\.?$', 'curt_response'),
    (r'\b(guess|suppose)\s+(so|not)\b', 'reluctant_agreement'),
    (r'\bif\s+you\s+say\s+so\b', 'passive_aggressive'),
    (r'\byeah\s+sure\b', 'sarcastic_agreement'),
    (r'\bdo\s+what(ever)?\s+you\s+want\b', 'dismissive'),
    (r'\bi\s+don.?t\s+care\b', 'disengagement'),
    (r'\bnever\s*mind\b', 'withdrawal'),
    (r'\bforget\s+it\b', 'withdrawal'),
    (r'\bwhy\s+do\s+i\s+(even|bother)\b', 'resentment'),
    (r'\bhere\s+we\s+go\s+again\b', 'contempt'),
    (r'\balways\b.*\b(do\s+this|the\s+same)\b', 'generalizing'),
    (r'\bnever\b.*\b(listen|care|help|change)\b', 'generalizing'),
    (r'\byou\s+should\s+(already|know)\b', 'expectation_setting'),
]

ESCALATION_PATTERNS = [
    (r'\bdon.?t\s+talk\s+to\s+me\b', 'stonewalling'),
    (r'\bi.?m\s+done\b', 'threatening_end'),
    (r'\bleave\s+me\s+alone\b', 'demanding_space'),
    (r'\bstop\s+texting\b', 'demanding_space'),
    (r'\bthis\s+is\s+(pointless|useless|going\s+nowhere)\b', 'invalidating'),
    (r'\bi\s+can.?t\s+(do\s+this|deal\s+with)\b', 'overwhelm'),
    (r'\byou\s+make\s+me\b', 'blame_shifting'),
    (r'\bif\s+you\s+(don.?t|can.?t)\b.*\b(then|i.?ll|i\s+will)\b', 'conditional_threat'),
    (r'\b(always|never)\s+\w+\s+(wrong|right|fault)\b', 'absolute_blame'),
    (r'\byou.?re\s+(always|never)\b', 'absolute_blame'),
    (r'\byou\s+(just|only)\s+care\s+about\b', 'accusation'),
    (r'\bwhy\s+can.?t\s+you\s+just\b', 'frustration_demand'),
]

POSITIVE_PATTERNS = [
    (r'\bi\s+love\s+you\b', 'affection'),
    (r'\bi\s+miss\s+you\b', 'longing'),
    (r'\bthank\s*you\b', 'gratitude'),
    (r'\bsorry\b', 'apology'),
    (r'\bi\s+appreciate\b', 'appreciation'),
    (r'\byou.?re\s+(right|correct)\b', 'validation'),
    (r'\bmy\s+bad\b', 'accountability'),
    (r'\bgood\s+(morning|night|evening)\b', 'daily_ritual'),
    (r'\bsweet\s+dreams\b', 'affection'),
    (r'\bhave\s+a\s+good\b', 'care'),
    (r'\bmiss\s+you\b', 'longing'),
    (r'\bcan.?t\s+wait\s+to\s+see\s+you\b', 'anticipation'),
]

TOPIC_PATTERNS = [
    (r'\bschedul\w*\b|\bwhat\s+time\b|\bwhen\s+(are|do|can|should|will)\b', 'scheduling'),
    (r'\bmom\b|\bdad\b|\bfamily\b|\bsister\b|\bbrother\b|\bparent\b', 'family'),
    (r'\bwork\b|\bjob\b|\bboss\b|\bclient\b|\boffice\b|\bmeeting\b', 'work'),
    (r'\bmoney\b|\bpay\b|\brent\b|\bbill\b|\bcost\b|\bexpens\w*\b', 'money'),
    (r'\bsex\b|\bintima\w*\b|\bcuddle\b|\bkiss\b', 'intimacy'),
    (r'\bstalk\w*\b|\begg\w*\b|\bporch\b|\bsafe\w*\b|\bpolic\w*\b', 'stalker_situation'),
    (r'\bhospital\b|\bseizure\b|\bsick\b|\bhealth\b|\bdoctor\b|\bmedic\w*\b', 'health'),
    (r'\btravel\b|\bflight\b|\bairport\b|\baustria\b|\btrip\b', 'travel'),
    (r'\btrust\b|\bhonest\w*\b|\blie\w*\b|\blying\b|\btruth\b', 'trust_issues'),
    (r'\bbreak\s*up\b|\bover\b.*\brelationship\b|\bdone\b.*\bwith\s+you\b', 'breakup_talk'),
]


def detect_tone_shift(messages, window=5):
    """
    Detect the transition point where a conversation goes from neutral/positive to negative.
    Returns the index of the first message that shifts tone.
    """
    if len(messages) < window:
        return None
    
    for i in range(window, len(messages)):
        # Look at window of messages ending at i
        recent = messages[max(0, i-window):i]
        neg_count = sum(1 for m in recent if m.get('_neg_score', 0) > 0)
        
        # If majority of recent window is negative and previous wasn't
        if neg_count >= window * 0.6:
            # Find the first negative in this window
            for j in range(max(0, i-window), i):
                if messages[j].get('_neg_score', 0) > 0:
                    return j
    return None


def analyze_message_patterns(body, direction):
    """Detect behavioral patterns in a message. Returns dict of findings."""
    if not body:
        return {}
    
    lower = body.lower().strip()
    findings = {}
    
    # Passive-aggressive
    for pattern, label in PASSIVE_AGGRESSIVE_PATTERNS:
        if re.search(pattern, lower):
            findings.setdefault('passive_aggressive', []).append(label)
    
    # Escalation
    for pattern, label in ESCALATION_PATTERNS:
        if re.search(pattern, lower):
            findings.setdefault('escalation', []).append(label)
    
    # Positive
    for pattern, label in POSITIVE_PATTERNS:
        if re.search(pattern, lower):
            findings.setdefault('positive', []).append(label)
    
    # Topics
    for pattern, label in TOPIC_PATTERNS:
        if re.search(pattern, lower):
            findings.setdefault('topics', []).append(label)
    
    return findings


def is_apology(body):
    """Check if message is an apology/conciliatory, not an attack."""
    if not body:
        return False
    lower = body.lower()
    apology_markers = [
        r'\b(i.?m |im |i am )?(really |so |truly |very )?(sorry|apologize|apologise)\b',
        r'\bmy bad\b', r'\bmy fault\b', r'\bi was wrong\b', r'\bi shouldn.?t have\b',
        r'\bi should have\b', r'\bforgive me\b', r'\bplease.*chance\b',
        r'\bi.?ll (do |try |be )better\b', r'\bi (messed|screwed|fucked) up\b',
        r'\byou.?re right\b', r'\byou were right\b',
    ]
    for pat in apology_markers:
        if re.search(pat, lower):
            return True
    return False


def is_self_directed(body):
    """Check if negativity is about self, not the other person."""
    if not body:
        return False
    lower = body.lower()
    self_patterns = [
        r'\bi.?m\s+(a |an |such a |the )?(shit|ass|idiot|stupid|terrible|worst|bad|awful|mess)',
        r'\bi\s+(suck|hate myself|messed up|screwed up|fucked up)\b',
        r'\bi\s+should\s+(shut up|stop|have)\b',
        r'\bmy fault\b', r'\bmy bad\b', r'\bi was wrong\b',
    ]
    for pat in self_patterns:
        if re.search(pat, lower):
            return True
    return False


def is_third_party_venting(body, prev_msgs=None):
    """Check if negativity is about work/family/outside situation, not partner."""
    if not body:
        return False
    lower = body.lower()
    # Talking about third parties
    third_party = [
        r'\b(my |the )?(worker|boss|client|customer|employee|coworker|colleague|manager|contractor|guy|tenant)\b',
        r'\b(this |that |the )?(job|work|company|business|office|site)\b.*\b(sucks?|terrible|awful|shit|fuck|annoying|ridiculous)\b',
        r'\b(my |the )?(car|truck|phone|computer|laptop)\b.*\b(broke|dead|fucked|shit)\b',
        r'\b(traffic|weather|subway|train|bus)\b.*\b(sucks?|awful|terrible|shit|fuck)\b',
    ]
    # Also check if "you/your" is absent when swearing — likely venting about something else
    has_you_ref = bool(re.search(r'\byou\b|\byour\b|\byou.?re\b|\byou.?ve\b|\byou.?ll\b', lower))
    
    for pat in third_party:
        if re.search(pat, lower):
            return True
    
    return False


def is_joke_context(msg_idx, all_msgs, window=3):
    """
    Check if a message is in a joking/playful context by looking at surrounding messages.
    Returns True if laughter/playful signals are nearby.
    """
    joke_signals = [
        r'(?:\b(?:lol|lmao|lmfao|haha+|rofl)\b|😂|🤣|😆|😹|💀)',
        r'^(?:lol|haha|lmao|😂)$',
        r'(?:\b(?:jk|just kidding|joking|kidding)\b)',
        r'(?:🤪|😜|😝|🤡|😏|😈|🙃|😂|🤣)',
    ]
    
    start = max(0, msg_idx - window)
    end = min(len(all_msgs), msg_idx + window + 1)
    
    laugh_count = 0
    for i in range(start, end):
        body = (all_msgs[i].get('body', '') or '').lower()
        for pat in joke_signals:
            if re.search(pat, body):
                laugh_count += 1
                break
    
    # If 2+ messages in the window have laugh signals, it's joking context
    return laugh_count >= 2


def is_de_escalation(body):
    """Check if a message is attempting to de-escalate / calm things down."""
    if not body:
        return False
    lower = body.lower()
    de_esc = [
        r'\b(let.?s |can we |we should )(stop|calm|relax|chill|drop it|move on|not fight|not argue)\b',
        r'\b(please |just )?(calm down|stop fighting|stop arguing|stop this|enough)\b',
        r'\bcan we (just |please )?(talk|discuss) (calmly|nicely|like adults|normally)\b',
        r'\bi don.?t want to (fight|argue)\b',
        r'\blet.?s not (fight|argue|do this)\b',
        r'\bcan we (move on|move past|drop)\b',
        r'\bi.?m (trying to|not trying to)\s*(fight|argue|upset you|make you mad)\b',
        r'\bleave me alone\b',  # disengagement = de-escalation attempt
        r'\bi need (a |some )?(space|break|minute|time)\b',
        r'\bplease stop\b',
        r'\blet.?s just\b.*\b(tomorrow|later|another time|sleep|rest)\b',
    ]
    for pat in de_esc:
        if re.search(pat, lower):
            return True
    return False


def is_banter(msg_idx, all_msgs, window=4):
    """
    Check if messages around this index are playful banter (both sides laughing/joking).
    Returns True if both people are engaged in light exchanges.
    """
    start = max(0, msg_idx - window)
    end = min(len(all_msgs), msg_idx + window + 1)
    
    banter_words = r'(?:\b(?:lol|lmao|haha+|omg|bruh|bro|dude)\b|😂|🤣|💀|😭|😆)'
    
    sent_laughing = False
    recv_laughing = False
    for i in range(start, end):
        m = all_msgs[i]
        body = (m.get('body', '') or '').lower()
        if re.search(banter_words, body):
            if m['direction'] == 'sent':
                sent_laughing = True
            else:
                recv_laughing = True
    
    return sent_laughing and recv_laughing


def is_expressing_hurt(body):
    """
    Check if message is expressing hurt, disappointment, or emotional pain
    rather than attacking. Saying 'sounds like you don't wanna see me' after
    being rejected/cancelled on is a normal human response, not hostility.
    """
    if not body:
        return False
    lower = body.lower()
    hurt_patterns = [
        # Expressing feeling unwanted/rejected
        r'\b(sounds like|feels like|seems like)\s+you\s+(don.?t|do not|doesn.?t)\s*(want|wanna|care|like|love|miss)',
        r'\byou\s+(don.?t|do not)\s+(want to|wanna)\s+(see|be with|talk to|hang out|spend time)',
        r'\byou\s+(don.?t|do not)\s+(want|wanna)\s+me\b',
        r'\byou\s+(don.?t|do not)\s+(miss|need|love)\s+me\b',
        r'\bi\s+(miss|love|need)\s+you\b',
        r'\bwish\s+you\s+would\b',
        r'\bi\s+wish\b.*\b(see|talk|time|together)\b',
        # Expressing sadness/helplessness about situation
        r'\bthis\s+(sucks|hurts|isn.?t fair|is hard)\b',
        r'\bi\s+(don.?t|do not)\s+know\s+what\s+to\s+(do|say)\b',
        r'\byou\s+(don.?t|do not)\s+know\s+what\s+to\s+do\b',
        r'\bwhat\s+(am|do)\s+i\s+supposed\s+to\b',
        r'\bi\s+(don.?t|do not)\s+want(a|\s+to)\s+(argue|fight|lose|bother|upset)\b',
        # Seeking reassurance
        r'\bare\s+you\s+(dumping|breaking|leaving|done with)\b',
        r'\bare\s+you\s+ok\b',
        r'\bplease\s+(don.?t|do not)\s+(dump|leave|break up|go)\b',
        r'\bi\s+hope\s+you.?(re|\s+are)\s+ok\b',
        # Expressing loneliness/wanting connection
        r'\bi\s+expect(ed)?\s+to\b.*\b(nice|good|great|time|see|together)\b',
        r'\bwaiting\s+to\s+spend\s+time\b',
        r'\bwant(ed)?\s+to\s+(see|be with|spend)\b',
        r'\bsorry\s+(i|im|i.?m)\s+(so\s+)?(tired|late|exhausted|sleepy|busy)\b',
        # Expressing hurt about being dismissed
        r'\byou.?re\s+not\s+(listening|hearing|understanding)\b',
        r'\bmaybe\s+(i|you)\s+(just|should)\b',
        r'\bidk\s+what\s+to\s+(say|do)\b',
    ]
    for pat in hurt_patterns:
        if re.search(pat, lower):
            return True
    return False


def is_legitimate_stressor_context(body, msg_idx, all_msgs, window=10):
    """
    Check if the person is dealing with legitimate stressors that explain
    frustration without it being hostility. Context: heavy work schedule,
    family caregiving (mom seizures, dad cancer), physical injuries, exhaustion.
    A person saying 'you don't know what to do' after working 14 hours and
    being told they're boring is NOT starting an argument.
    """
    if not body:
        return False
    lower = body.lower()
    
    # Check surrounding messages for stressor context
    start = max(0, msg_idx - window)
    end = min(len(all_msgs), msg_idx + window)
    context = ' '.join((all_msgs[i].get('body', '') or '').lower() for i in range(start, end))
    
    stressor_context = [
        r'\b(tired|exhausted|sleepy|sleep|rest|nap|fell\s+asleep|woke\s+up)\b',
        r'\b(work|install|job|client|project|hours|shift|overtime|cabinet)\b',
        r'\b(mom|dad|seizure|cancer|hospital|doctor|surgery|broken\s+rib|caregiver)\b',
        r'\b(hurt|injury|back\s+pain|hemorrhoid|dizzy|sick)\b',
        r'\b(stalk|stalker|creep|porch|camera|police)\b',
        r'\b(sister|passed\s+away|funeral|death|grief|mourning)\b',
    ]
    
    stressor_hits = sum(1 for pat in stressor_context if re.search(pat, context))
    
    # If 2+ stressor categories are present in the window, person is under real pressure
    return stressor_hits >= 2


def score_negativity(body):
    """
    Raw negativity score 0-5. Used for initial screening.
    This is the RAW score before context adjustments.
    """
    if not body:
        return 0
    lower = body.lower()
    score = 0
    
    # Strong negative directed at partner
    if re.search(r'\bfuck\s+you\b|\bhate\s+you\b|\byou.?re\s+(pathetic|worthless|stupid|useless|crazy|insane)\b', lower):
        score += 3
    if re.search(r'\bshut\s+(the fuck )?up\b|\bgo\s+away\b', lower):
        score += 2
    # Moderate negative
    if re.search(r'\bfuck\w*\b|\bshit\w*\b|\bbullshit\b|\bdamn\b', lower):
        score += 1
    if re.search(r'\byou\s+(always|never)\b|\byou\s+(don.?t|can.?t|won.?t)\b', lower):
        score += 1
    if re.search(r'\bwhy\s+(do|can.?t|won.?t|don.?t)\s+you\b', lower):
        score += 1
    # Dismissive standalone
    if re.search(r'^(k|ok|fine|whatever|sure|bye)\.?$', lower):
        score += 1
    
    return min(score, 5)


def score_directed_hostility(msg, msg_idx, all_msgs):
    """
    Context-aware hostility score. Only scores REAL hostility directed at the partner.
    Returns 0 if it's a joke, self-directed, third-party venting, or apology.
    This is the KEY function that prevents false positives.
    """
    body = msg.get('body', '')
    if not body:
        return 0
    
    raw = score_negativity(body)
    if raw == 0:
        return 0
    
    # ── FILTERS: things that look negative but aren't arguments ──
    # IMPORTANT: Filters 1-5 only apply to MILD hostility (raw <= 2).
    # If raw >= 3, the message is intense enough ("fuck you", "you're pathetic")
    # that it MUST be scored regardless of context.
    
    # 1) Apology — "I'm sorry I should have shut up" is NOT hostile
    if is_apology(body):
        return 0
    
    # 2) Self-directed — "I'm a shithead" is not attacking partner
    if is_self_directed(body):
        return 0
    
    # 3) Third-party venting — "my workers are shit" is not about partner
    #    But ONLY for mild stuff. "fuck you" is never third-party.
    if raw <= 2 and is_third_party_venting(body):
        return 0
    
    # 4) Joke context — both people laughing around this message
    #    Only for mild stuff. "fuck you" in a joke is still hostile enough to count.
    if raw <= 2 and is_joke_context(msg_idx, all_msgs, window=3):
        return 0
    
    # 5) Expressing hurt/disappointment — "sounds like you don't wanna see me"
    #    Only for mild/moderate. Does NOT filter "fuck you" or "you're crazy".
    if raw <= 2 and is_expressing_hurt(body):
        return 0
    
    # 6) "Leave me alone" / de-escalation — reduce score, it's withdrawal not attack
    if is_de_escalation(body):
        return max(1, raw - 1)  # still mildly negative but not "starting" a fight
    
    # 7) Legitimate stressor context — if person is exhausted from work, dealing
    #    with family health crisis, injuries etc., mild frustration is understandable
    #    and shouldn't be scored as starting a fight. Only for mild stuff (raw <= 2).
    if raw <= 2 and is_legitimate_stressor_context(body, msg_idx, all_msgs):
        return max(0, raw - 1)
    
    # 8) Check if "you" is even referenced — swearing without "you" is often venting
    lower = body.lower()
    has_you = bool(re.search(r'\byou\b|\byour\b|\byou.?re\b|\byou.?ve\b|\byou.?ll\b', lower))
    
    # Strong hostility WITH "you" = definitely directed
    if raw >= 3 and has_you:
        return raw
    
    # Strong hostility WITHOUT "you" — still counts but slightly reduced
    # "fuck this bullshit" during a fight is still hostile
    if raw >= 3 and not has_you:
        return raw - 1
    
    # Moderate negativity WITH "you" = probably directed
    if raw >= 2 and has_you:
        return raw
    
    # Swearing WITHOUT "you" = likely venting, halve it
    if not has_you and raw <= 2:
        return max(0, raw - 1)
    
    return raw


def score_provocation(body):
    """
    Score how PROVOCATIVE a message is — even if it doesn't contain swear words.
    Provocations include:
    - Accusations ("you did this on purpose", "you fuck me over")
    - Dismissals ("you don't know what you're doing", "you don't care")
    - Minimizing ("it's not that hard", "everyone else can do it")
    - Ultimatums ("if you can't ___ then ___")
    - Character attacks ("you're unreliable", "you don't put effort in")
    - Canceling/withdrawing ("fine then don't come", "correct" to dumping)
    - Guilt-tripping ("I'm still talking to you after all that")
    - Accusing of lying/manipulation ("you did this on purpose", "you're gaslighting")
    - Bringing up past grievances as weapons
    
    Returns 0-4 provocation score.
    """
    if not body:
        return 0
    lower = body.lower()
    score = 0
    
    # Direct accusations
    if re.search(r'you\s+(did|do)\s+(this|that|it)\s+on\s+purpose', lower):
        score += 3
    if re.search(r'you\s+(fuck|screw|mess)\s+(me|us|everything)\s+(over|up)', lower):
        score += 3
    if re.search(r'you\s+(lied|lie|lying|manipulat)', lower):
        score += 2
    if re.search(r'you\s+(don.?t|never|didn.?t)\s+(care|listen|try|help|support|show up|stand up|prioriti)', lower):
        score += 2
    if re.search(r'you\s+(don.?t|never)\s+(put|make|give)\s+(any|an|zero|no)\s*(effort|time|energy|priority)', lower):
        score += 2
    if re.search(r'you\s+(always|constantly|keep|never stop)\s+(cancel|flake|bail|disappoint|let me down|push me away)', lower):
        score += 2
    
    # Character attacks / dismissals
    if re.search(r'you\s+(don.?t|do not)\s+(even\s+)?(know|understand|see|get|realize)', lower):
        score += 1
    if re.search(r'you.?re\s+(unreliable|selfish|awful|terrible|the\s+problem|the\s+worst)', lower):
        score += 2
    if re.search(r'you\s+(don.?t|never|didn.?t)\s+(appreciate|acknowledge|admit|recognize)', lower):
        score += 2
    if re.search(r'(it.?s|that.?s)\s+(not that|not even|really not)\s+(hard|difficult|complicated)', lower):
        score += 1
    if re.search(r'everyone\s+else\s+(can|does|would)', lower):
        score += 1
    
    # Guilt-tripping
    if re.search(r'(i.?m|I am)\s+still\s+(here|talking|trying|with you)', lower):
        score += 1
    if re.search(r'that.?s\s+(compassion|love|patience|effort)', lower):
        score += 1
    if re.search(r'after\s+(everything|all|what)\s+(i|I)\s+(did|do|gave|done|sacrificed)', lower):
        score += 1
    
    # Ultimatums / threatening end
    if re.search(r'(fine\s+then|okay\s+then)\s+(don.?t|leave|go|bye|whatever)', lower):
        score += 2
    if re.search(r'maybe\s+(we|you)\s+should\s+(just|break|stop|end)', lower):
        score += 2
    if re.search(r'i\s+(didn.?t|don.?t)\s+shut\s+up\s+fast\s+enough', lower):
        score += 2
    
    # Accusing of punishment/control
    if re.search(r'you\s+(cancel|did this)\s+to\s+punish', lower):
        score += 3
    if re.search(r'because\s+i\s+didn.?t\s+do\s+what\s+you\s+want', lower):
        score += 2
    
    # Minimizing partner's situation
    if re.search(r'you\s+(just|only)\s+want\s+(me\s+to|to)\s+(shut|stop|be quiet|drop|accept)', lower):
        score += 2
    if re.search(r'without\s+putting\s+in\s+(an\s+ounce|any|zero|no)\s*(of)?\s*(work|effort)', lower):
        score += 2
    
    # Sarcastic apologies (weaponized "sorry")
    if re.search(r'sorry\s+(i|that i)\s+(didn.?t|got|couldn.?t|freaked|had)', lower) and re.search(r'(shut up|fall down|freak|trash|upset)', lower):
        score += 2
    
    # Passive-aggressive "It was all my fault" / sarcastic agreement
    if re.search(r'(it was|it.?s)\s+all\s+my\s+fault', lower):
        score += 2
    if re.search(r'(right|sure|okay),?\s+(it.?s|I.?m)\s+(all|always|never)\s+(my|the)', lower):
        score += 1
    
    # Dismissing someone's work/abilities/intelligence
    if re.search(r'you\s+(don.?t|do not)\s+(even\s+)?(know|have)\s+(what|the)\s+(you.?re|basics)', lower):
        score += 2
    if re.search(r'(it.?s|that.?s)\s+got\s+you\s+convinced', lower):
        score += 2
    if re.search(r'you\s+(have|got)\s+(nothing|something)\s+worthwhile', lower):
        score += 2
    if re.search(r'you\s+(don.?t|do not)\s+have\s+(something|anything)\s+worth', lower):
        score += 2
    if re.search(r'you\s+don.?t\s+even\s+know', lower):
        score += 2
    
    # Blaming directly ("this is your fault", "because of you")
    if re.search(r'(this|that|it)\s+is\s+your\s+fault', lower):
        score += 3
    if re.search(r'(this|that).?s\s+your\s+fault', lower):
        score += 3
    if re.search(r'\byour\s+fault\b', lower):
        score += 2
    
    # Telling someone they're hostile/aggressive when they're not
    if re.search(r'you\s+(were|are|being)\s+(actively\s+)?(hostile|aggressive|mean|cruel|awful|nasty)', lower):
        score += 2
    if re.search(r'you\s+treated\s+me\s+like\s+(i was|a|I.?m)\s+(a\s+)?(jerk|idiot|moron|nothing|garbage|shit|trash)', lower):
        score += 2
    
    # "You drive everyone away" / catastrophizing about partner
    if re.search(r'you.?re\s+alone\s+because\s+you', lower):
        score += 3
    if re.search(r'you\s+drive\s+everyone\s+away', lower):
        score += 3
    if re.search(r'you\s+(always|constantly|keep)\s+(push|drive|scare)\s+(me|people|everyone)\s+away', lower):
        score += 2
    
    # Bringing up past wrongs as weapons
    if re.search(r'(your|you)\s+(family|parents|dad|mom)\s+(fucked|screwed|messed|let)', lower):
        score += 2
    if re.search(r'you\s+(went back|broke|violated)\s+(on|our)\s+(agreement|promise|deal)', lower):
        score += 2
    
    return min(score, 4)


def detect_argument_blocks(day_messages):
    """
    Identify genuine arguments in a day's messages.
    
    A GENUINE argument requires:
    - MUTUAL hostility: both people are being hostile to each other
      OR one person is hostile and the other is clearly upset/defensive
    - NOT jokes, venting about third parties, self-deprecation, or apologies
    - Sustained over multiple messages (not a single swear word)
    
    Returns list of blocks with:
      - start_idx, end_idx, is_argument, initiator, trigger_msg, trigger_time, trigger_idx
      - de_escalation_attempts: [{idx, direction, body, timestamp_ms}]
      - escalation_after_deesc: minutes the other person kept going after de-escalation
      - argument_topic_you, argument_topic_her: what each person is upset about
    """
    if not day_messages:
        return []
    
    # Score all messages with BOTH raw and context-aware scores
    for i, msg in enumerate(day_messages):
        msg['_neg_score'] = score_negativity(msg.get('body', ''))
        msg['_hostility'] = score_directed_hostility(msg, i, day_messages)
        msg['_is_deesc'] = is_de_escalation(msg.get('body', ''))
        msg['_is_apology'] = is_apology(msg.get('body', ''))
        msg['_is_banter'] = is_banter(i, day_messages)
    
    # ── Step 1: Find heated regions using DIRECTED hostility (not raw swear count) ──
    WINDOW = 16  # wider window so neutral filler ("ok", "what") doesn't dilute real fights
    THRESHOLD = 0.3  # lower threshold — even a few hostile messages in 16 = real argument
    is_heated = [False] * len(day_messages)
    
    for i in range(len(day_messages)):
        start = max(0, i - WINDOW // 2)
        end = min(len(day_messages), i + WINDOW // 2)
        window_msgs = day_messages[start:end]
        avg_hostility = sum(m['_hostility'] for m in window_msgs) / max(len(window_msgs), 1)
        if avg_hostility >= THRESHOLD:
            is_heated[i] = True
    
    # ── Step 2: Check participation — at least one side clearly hostile ──
    # Allow one-sided tirades: if one person sends 3+ hostile messages in the window,
    # that's an argument even if the other side only says "ok" / withdraws / de-escalates.
    for i in range(len(day_messages)):
        if not is_heated[i]:
            continue
        start = max(0, i - WINDOW)
        end = min(len(day_messages), i + WINDOW)
        window_msgs = day_messages[start:end]
        
        sent_hostile_count = sum(1 for m in window_msgs if m['direction'] == 'sent' and m['_hostility'] > 0)
        recv_hostile_count = sum(1 for m in window_msgs if m['direction'] == 'received' and m['_hostility'] > 0)
        
        sent_hostile = sent_hostile_count > 0
        recv_hostile = recv_hostile_count > 0
        
        # Also count as argument if one side is hostile and other is defensive/upset
        sent_defensive = any(m.get('_is_deesc') or m.get('_is_apology') for m in window_msgs if m['direction'] == 'sent')
        recv_defensive = any(m.get('_is_deesc') or m.get('_is_apology') for m in window_msgs if m['direction'] == 'received')
        
        # Also count as argument if one side has curt single-word responses during other's tirade
        sent_curt = sum(1 for m in window_msgs if m['direction'] == 'sent' and 
                       re.match(r'^(k|ok|fine|whatever|sure|bye|goodnight|good night|stop|enough|wow|smh|lol|mhm|yep|yea|nah|no|yes)\s*\.?$', (m.get('body', '') or '').lower().strip()))
        recv_curt = sum(1 for m in window_msgs if m['direction'] == 'received' and 
                       re.match(r'^(k|ok|fine|whatever|sure|bye|goodnight|good night|stop|enough|wow|smh|lol|mhm|yep|yea|nah|no|yes)\s*\.?$', (m.get('body', '') or '').lower().strip()))
        
        mutual = (sent_hostile and recv_hostile)
        one_attacks_other_defends = (sent_hostile and recv_defensive) or (recv_hostile and sent_defensive)
        one_sided_tirade = (sent_hostile_count >= 3 and (recv_curt >= 2 or recv_defensive)) or \
                          (recv_hostile_count >= 3 and (sent_curt >= 2 or sent_defensive))
        
        if not (mutual or one_attacks_other_defends or one_sided_tirade):
            is_heated[i] = False
    
    # ── Step 3: Build blocks ──
    blocks = []
    current_block = None
    
    for i, msg in enumerate(day_messages):
        heated = is_heated[i]
        
        if current_block is None:
            current_block = {
                'start_idx': i,
                'is_argument': heated,
                'messages': [msg],
            }
        elif heated != current_block['is_argument']:
            current_block['end_idx'] = i - 1
            blocks.append(current_block)
            current_block = {
                'start_idx': i,
                'is_argument': heated,
                'messages': [msg],
            }
        else:
            current_block['messages'].append(msg)
    
    if current_block:
        current_block['end_idx'] = len(day_messages) - 1
        blocks.append(current_block)
    
    # ── Step 4: For argument blocks, find who ACTUALLY started it ──
    # The old approach just found the first hostile message. But that often
    # catches the REACTOR, not the PROVOKER. Now we:
    #   a) Look 30 messages back for the provocation that caused the argument
    #   b) Score PROVOCATION (accusations, dismissals, guilt-tripping etc.)
    #   c) If the first "hostile" message is a RESPONSE to a provocation
    #      from the other side, attribute initiation to the provoker
    for block in blocks:
        if not block['is_argument']:
            continue
        
        # Wider search window: 30 before block + first 15 in block
        search_start = max(0, block['start_idx'] - 30)
        search_end = min(len(day_messages), block['start_idx'] + 15)
        search_msgs = day_messages[search_start:search_end]
        
        # Score every message in the window for BOTH hostility AND provocation
        for si, m in enumerate(search_msgs):
            m['_provocation'] = score_provocation(m.get('body', ''))
        
        # Find the first SIGNIFICANT provocation or hostility (the real trigger)
        # A provocation score >= 2 counts as "starting it" even without swearing
        # NOTE: h=0 messages (apologies, de-escalation) are NEVER triggers.
        first_hostile = None    # first hostility >= 1
        first_strong = None     # first hostility >= 2
        first_provoke = None    # first provocation >= 2
        
        for si, m in enumerate(search_msgs):
            abs_idx = search_start + si
            h = m.get('_hostility', 0)
            p = m.get('_provocation', 0)
            # Skip apologies and de-escalation as potential triggers
            if m.get('_is_apology') or m.get('_is_deesc'):
                continue
            if first_hostile is None and h >= 1:
                first_hostile = (m, abs_idx, 'hostility')
            if first_strong is None and h >= 2:
                first_strong = (m, abs_idx, 'hostility')
            if first_provoke is None and p >= 2:
                first_provoke = (m, abs_idx, 'provocation')
        
        # Determine the TRUE initiator:
        # Priority 1: Whoever provoked first (provocation >= 2) — even without swearing
        # Priority 2: If provocation came from one side and hostility from the other,
        #             the provoker started it (the hostile response is a reaction)
        # Priority 3: First strong hostility (>= 2)
        # Priority 4: First mild hostility (>= 1) — BUT only if no prior provocation
        #             from the other side (provocation >= 1 OR dismissive content)
        
        trigger = None
        trigger_abs_idx = None
        
        if first_provoke and first_strong:
            prov_msg, prov_idx, _ = first_provoke
            host_msg, host_idx, _ = first_strong
            
            # If provocation came BEFORE or AT the hostile message from the OTHER side,
            # the provoker is the initiator
            if prov_idx <= host_idx and prov_msg['direction'] != host_msg['direction']:
                trigger = prov_msg
                trigger_abs_idx = prov_idx
            elif prov_idx <= host_idx:
                # Same side provoked and was hostile — they definitely started it
                trigger = prov_msg
                trigger_abs_idx = prov_idx
            else:
                # Hostility came first, then provocation — the hostile person started
                trigger = host_msg
                trigger_abs_idx = host_idx
        elif first_provoke:
            trigger = first_provoke[0]
            trigger_abs_idx = first_provoke[1]
        elif first_strong:
            trigger = first_strong[0]
            trigger_abs_idx = first_strong[1]
        elif first_hostile:
            # Before assigning mild hostility (h=1) as trigger, thoroughly check
            # if the OTHER side provoked it. Many h=1 reactions are responses to:
            # - Dismissals, accusations, guilt-tripping, character attacks
            # - Canceling plans, minimizing, questioning motives
            # - Any negative content directed at the partner
            host_msg, host_idx, _ = first_hostile
            prior_provoke = None
            
            for si, m in enumerate(search_msgs):
                abs_idx = search_start + si
                if abs_idx >= host_idx:
                    break
                if m['direction'] == host_msg['direction']:
                    continue  # same side, skip
                    
                # Check provocation patterns
                if m.get('_provocation', 0) >= 1:
                    prior_provoke = (m, abs_idx)
                    break
                
                # Check for dismissive/accusatory content that provocation patterns
                # might miss: questioning character, doubting, pushing buttons
                body_lower = (m.get('body', '') or '').lower()
                if re.search(r'you\\s+(don.?t|can.?t|won.?t|never|didn.?t|aren.?t)', body_lower) and \
                   re.search(r'(know|care|try|listen|understand|appreciate|acknowledge|realize|get it|show|plan|effort|change)', body_lower):
                    prior_provoke = (m, abs_idx)
                    break
                if re.search(r'(your fault|you.?re wrong|you.?re the|because of you|blame you)', body_lower):
                    prior_provoke = (m, abs_idx)
                    break
                # Hostile questions that imply fault
                if re.search(r'(why\\s+(do|did|can.?t|don.?t|won.?t)\\s+you|what.?s wrong with you|are you serious)', body_lower):
                    prior_provoke = (m, abs_idx)
                    break
            
            if prior_provoke:
                trigger = prior_provoke[0]
                trigger_abs_idx = prior_provoke[1]
            else:
                trigger = host_msg
                trigger_abs_idx = host_idx
        
        if trigger:
            block['initiator'] = trigger['direction']
            block['trigger_msg'] = trigger.get('body', '')[:200]
            block['trigger_time'] = trigger.get('time', '')
            block['trigger_idx'] = trigger_abs_idx
        else:
            block['initiator'] = 'unclear'
            block['trigger_msg'] = ''
            block['trigger_time'] = ''
            block['trigger_idx'] = block['start_idx']
        
        # ── Step 5: Track de-escalation attempts and persistence ──
        block['de_escalation_attempts'] = []
        block['escalation_after_deesc_minutes'] = 0
        block['refused_deesc_by'] = None
        
        for mi in range(block['start_idx'], block['end_idx'] + 1):
            m = day_messages[mi]
            if m.get('_is_deesc') or m.get('_is_apology'):
                block['de_escalation_attempts'].append({
                    'idx': mi,
                    'direction': m['direction'],
                    'body': (m.get('body', '') or '')[:150],
                    'timestamp_ms': m.get('timestamp_ms', 0),
                    'time': m.get('time', ''),
                })
        
        # Check if someone kept going after the other tried to de-escalate
        if block['de_escalation_attempts']:
            first_deesc = block['de_escalation_attempts'][0]
            deesc_by = first_deesc['direction']  # who tried to de-escalate
            other_side = 'received' if deesc_by == 'sent' else 'sent'
            deesc_ts = first_deesc['timestamp_ms']
            
            # Find the LAST hostile message from the OTHER side after de-escalation
            last_hostile_ts = 0
            for mi in range(first_deesc['idx'] + 1, min(block['end_idx'] + 1, len(day_messages))):
                m = day_messages[mi]
                if m['direction'] == other_side and m.get('_hostility', 0) >= 1:
                    last_hostile_ts = m.get('timestamp_ms', 0)
            
            # Also look beyond the block for continued hostility (up to 30 messages)
            extended_end = min(len(day_messages), block['end_idx'] + 30)
            for mi in range(block['end_idx'] + 1, extended_end):
                m = day_messages[mi]
                if m['direction'] == other_side and m.get('_hostility', 0) >= 1:
                    last_hostile_ts = m.get('timestamp_ms', 0)
                elif m['direction'] == other_side and m.get('_hostility', 0) == 0:
                    # They calmed down
                    break
            
            if deesc_ts and last_hostile_ts and last_hostile_ts > deesc_ts:
                minutes_after = (last_hostile_ts - deesc_ts) / 60000
                block['escalation_after_deesc_minutes'] = round(minutes_after, 1)
                block['refused_deesc_by'] = other_side
        
        # ── Step 6: Detect what each person is upset about ──
        block['argument_topic_you'] = detect_upset_topic(
            [day_messages[mi] for mi in range(block['start_idx'], block['end_idx'] + 1) if day_messages[mi]['direction'] == 'sent']
        )
        block['argument_topic_her'] = detect_upset_topic(
            [day_messages[mi] for mi in range(block['start_idx'], block['end_idx'] + 1) if day_messages[mi]['direction'] == 'received']
        )
    
    # ── Step 7: Merge adjacent/overlapping argument blocks within 15 minutes ──
    merged_blocks = []
    for block in blocks:
        if not block['is_argument']:
            merged_blocks.append(block)
            continue
        
        if merged_blocks and merged_blocks[-1]['is_argument']:
            prev = merged_blocks[-1]
            # Check time gap between end of prev block and start of current
            prev_end_ts = day_messages[prev['end_idx']].get('timestamp_ms', 0)
            curr_start_ts = day_messages[block['start_idx']].get('timestamp_ms', 0)
            gap_minutes = (curr_start_ts - prev_end_ts) / 60000 if prev_end_ts and curr_start_ts else 999
            
            if gap_minutes <= 15:
                # Merge: extend previous block to include this one
                prev['end_idx'] = block['end_idx']
                prev['messages'] = day_messages[prev['start_idx']:prev['end_idx'] + 1]
                # Keep the earlier trigger (the one who started it first)
                # Merge de-escalation attempts
                prev['de_escalation_attempts'] = prev.get('de_escalation_attempts', []) + block.get('de_escalation_attempts', [])
                # Recalculate escalation persistence from combined block
                if block.get('escalation_after_deesc_minutes', 0) > prev.get('escalation_after_deesc_minutes', 0):
                    prev['escalation_after_deesc_minutes'] = block['escalation_after_deesc_minutes']
                    prev['refused_deesc_by'] = block.get('refused_deesc_by')
                # Merge topics
                for key in ('argument_topic_you', 'argument_topic_her'):
                    prev_topic = prev.get(key, '')
                    curr_topic = block.get(key, '')
                    if curr_topic and curr_topic not in prev_topic:
                        prev[key] = f"{prev_topic}, {curr_topic}" if prev_topic else curr_topic
                continue
        
        merged_blocks.append(block)
    
    # ── Step 8: Deduplicate blocks with identical timestamps ──
    deduped = []
    seen_triggers = set()
    for block in merged_blocks:
        if block['is_argument']:
            key = (block.get('trigger_time', ''), block.get('trigger_msg', '')[:50])
            if key in seen_triggers:
                continue  # skip duplicate
            seen_triggers.add(key)
        deduped.append(block)
    
    return deduped


def detect_upset_topic(msgs):
    """
    Analyze a set of messages from one person during an argument to find
    what they're upset about. Returns a short description.
    """
    if not msgs:
        return ''
    
    combined = ' '.join((m.get('body', '') or '') for m in msgs).lower()
    
    UPSET_TOPICS = [
        (r'\blate\b|\bon time\b|\bshowed up\b.*\b(late|hour|minute)\b|\bwaiting\b.*\b(for you|all day)\b', 'lateness/tardiness'),
        (r'\b(dismiss|dismissive|don.?t care|doesn.?t care|ignor|ignored|ignoring)\b', 'feeling dismissed/ignored'),
        (r'\b(not listen|don.?t listen|never listen|won.?t listen|aren.?t listening)\b', 'not listening'),
        (r'\b(control|controlling|tell me what|boss me|let me|allow me|my decision)\b', 'controlling behavior'),
        (r'\b(promise|promised|broke.*promise|said you would|you said)\b', 'broken promises'),
        (r'\b(trust|honest|lie|lied|lying|truth|cheat)\b', 'trust issues'),
        (r'\b(respect|disrespect|rude|mean to me)\b', 'feeling disrespected'),
        (r'\b(help|never help|don.?t help|won.?t help|all by myself|do everything)\b', 'lack of help/effort'),
        (r'\b(family|mom|dad|mother|father|sister|brother|parent)\b', 'family issues'),
        (r'\b(money|pay|owe|rent|bill|afford|expensive|broke)\b', 'money issues'),
        (r'\b(time|spend time|see you|see me|hanging out|come over|visit)\b', 'wanting more time together'),
        (r'\b(phone|text|respond|reply|answer|call back|ghosting|left on read)\b', 'communication/response time'),
        (r'\b(priority|prioritize|important|matter|care about)\b', 'not feeling like a priority'),
        (r'\b(space|alone|smother|clingy|need.*break|back off)\b', 'needing space'),
        (r'\b(stalk|stalker|creep|following|watching|porch|car outside)\b', 'stalker situation'),
        (r'\b(attack|yell|scream|tone|voice|calm down)\b', 'tone/aggression'),
        (r'\b(apologize|apology|sorry|admit|acknowledge|own up)\b', 'wanting an apology/accountability'),
    ]
    
    found_topics = []
    for pattern, label in UPSET_TOPICS:
        if re.search(pattern, combined):
            found_topics.append(label)
    
    return ', '.join(found_topics[:3]) if found_topics else 'general frustration'


def detect_banter_blocks(day_messages):
    """
    Find stretches of playful banter/joking between both people.
    Returns list of {'start_idx', 'end_idx', 'msg_count', 'duration_minutes'}.
    """
    if not day_messages:
        return []
    
    banter_signals = r'(?:\b(?:lol|lmao|lmfao|haha+|rofl|omg|bruh|dude|bro|jk|kidding|joking)\b|😂|🤣|😆|💀|🤪|😜|😝|🙃|😏|😈|🤡|😭)'
    
    # Mark messages that are part of playful exchange
    is_playful = [False] * len(day_messages)
    for i in range(len(day_messages)):
        body = (day_messages[i].get('body', '') or '').lower()
        if re.search(banter_signals, body):
            is_playful[i] = True
    
    # Find stretches where both sides are laughing within a window
    banter_regions = [False] * len(day_messages)
    WINDOW = 6
    for i in range(len(day_messages)):
        start = max(0, i - WINDOW // 2)
        end = min(len(day_messages), i + WINDOW // 2)
        window = day_messages[start:end]
        
        sent_laughing = any(is_playful[j] for j in range(start, end) if day_messages[j]['direction'] == 'sent')
        recv_laughing = any(is_playful[j] for j in range(start, end) if day_messages[j]['direction'] == 'received')
        
        playful_count = sum(1 for j in range(start, end) if is_playful[j])
        
        if sent_laughing and recv_laughing and playful_count >= 2:
            banter_regions[i] = True
    
    # Build blocks
    blocks = []
    current = None
    for i in range(len(day_messages)):
        if banter_regions[i]:
            if current is None:
                current = {'start_idx': i}
            current['end_idx'] = i
        else:
            if current is not None:
                msg_count = current['end_idx'] - current['start_idx'] + 1
                if msg_count >= 3:  # minimum 3 messages to count as banter
                    ts_start = day_messages[current['start_idx']].get('timestamp_ms', 0)
                    ts_end = day_messages[current['end_idx']].get('timestamp_ms', 0)
                    duration = (ts_end - ts_start) / 60000 if ts_start and ts_end else 0
                    current['msg_count'] = msg_count
                    current['duration_minutes'] = round(duration, 1)
                    blocks.append(current)
                current = None
    
    if current is not None:
        msg_count = current['end_idx'] - current['start_idx'] + 1
        if msg_count >= 3:
            ts_start = day_messages[current['start_idx']].get('timestamp_ms', 0)
            ts_end = day_messages[current['end_idx']].get('timestamp_ms', 0)
            duration = (ts_end - ts_start) / 60000 if ts_start and ts_end else 0
            current['msg_count'] = msg_count
            current['duration_minutes'] = round(duration, 1)
            blocks.append(current)
    
    return blocks


def classify_day_mood(day_messages, blocks):
    """Classify the overall day mood based on message patterns."""
    if not day_messages:
        return 'no_contact'
    
    total_neg = sum(m.get('_neg_score', 0) for m in day_messages)
    avg_neg = total_neg / max(len(day_messages), 1)
    argument_blocks = [b for b in blocks if b['is_argument']]
    total_positive = sum(1 for m in day_messages if m.get('_patterns', {}).get('positive'))
    
    if avg_neg >= 1.5 or len(argument_blocks) >= 2:
        return 'explosive'
    elif avg_neg >= 0.8 or len(argument_blocks) >= 1:
        return 'heated'
    elif avg_neg >= 0.3:
        return 'tense'
    elif total_positive > len(day_messages) * 0.1:
        return 'loving'
    else:
        return 'neutral'


def detect_conversation_gaps(day_messages):
    """Find significant time gaps within a day (>2 hours) that separate conversation sessions."""
    gaps = []
    for i in range(1, len(day_messages)):
        prev_ts = day_messages[i-1].get('timestamp_ms', 0)
        curr_ts = day_messages[i].get('timestamp_ms', 0)
        if prev_ts and curr_ts:
            diff_min = (curr_ts - prev_ts) / 60000
            if diff_min >= 120:  # 2+ hour gap
                gaps.append({
                    'after_idx': i - 1,
                    'before_idx': i,
                    'gap_minutes': int(diff_min),
                    'gap_str': f"{int(diff_min//60)}h{int(diff_min%60):02d}m",
                })
    return gaps


# ──────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────────────────────────────────────

import xml.etree.ElementTree as ET
try:
    import defusedxml.ElementTree as SafeET
except ImportError:
    SafeET = None  # Fall back to stdlib if defusedxml not installed
import sqlite3

def phone_match(number):
    if not number:
        return False
    clean = re.sub(r'[^\d]', '', number)
    return clean.endswith(PHONE_SUFFIX)

def load_all_data():
    """Load all data sources and merge into a per-day structure."""
    print("Loading Signal Desktop messages...")
    # Guard against extremely large JSON files (500MB limit)
    json_size = os.path.getsize(SIGNAL_DESKTOP_JSON)
    if json_size > 500 * 1024 * 1024:
        raise RuntimeError(f"JSON file too large ({json_size / 1024 / 1024:.0f}MB > 500MB limit)")
    with open(SIGNAL_DESKTOP_JSON, 'r', encoding='utf-8') as f:
        desktop_data = json.load(f)
    
    # Organize by date
    days = defaultdict(lambda: {
        'signal_messages': [],
        'sms_messages': [],
        'phone_calls': [],
        'signal_calls': [],
    })
    
    for msg in desktop_data.get('messages', []):
        if msg.get('type') not in ('incoming', 'outgoing'):
            continue  # skip call-history, notifications, etc.
        ts_str = msg.get('timestamp', '')
        if not ts_str or ts_str == 'unknown':
            continue
        try:
            dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            continue
        
        date = dt.strftime('%Y-%m-%d')
        days[date]['signal_messages'].append({
            'time': dt.strftime('%H:%M:%S'),
            'timestamp_ms': msg.get('timestamp_ms', 0),
            'direction': msg.get('direction', 'unknown'),
            'body': msg.get('body', ''),
            'has_attachments': msg.get('has_attachments', False),
            'source': 'signal',
        })
    
    # Load SMS
    print("Loading SMS messages...")
    try:
        _parse = SafeET.iterparse if SafeET else ET.iterparse
        context = _parse(SMS_XML, events=('end',))
        for event, elem in context:
            if elem.tag == 'sms':
                addr = elem.get('address', '')
                if phone_match(addr):
                    msg_type = elem.get('type', '')
                    body = elem.get('body', '')
                    date_ms = int(elem.get('date', '0'))
                    dt = datetime.fromtimestamp(date_ms / 1000)
                    date = dt.strftime('%Y-%m-%d')
                    
                    direction = 'sent' if msg_type == '2' else 'received'
                    days[date]['sms_messages'].append({
                        'time': dt.strftime('%H:%M:%S'),
                        'timestamp_ms': date_ms,
                        'direction': direction,
                        'body': body,
                        'source': 'sms',
                    })
                elem.clear()
    except Exception as e:
        print(f"  SMS error: {e}")
    
    # Load phone calls
    print("Loading phone calls...")
    try:
        _tree_parse = SafeET.parse if SafeET else ET.parse
        tree = _tree_parse(CALLS_XML)
        root = tree.getroot()
        for call in root.findall('.//call'):
            number = call.get('number', '')
            if phone_match(number):
                date_ms = int(call.get('date', '0'))
                dt = datetime.fromtimestamp(date_ms / 1000)
                date = dt.strftime('%Y-%m-%d')
                call_type = call.get('type', '0')
                duration = int(call.get('duration', '0'))
                
                direction_map = {'1': 'incoming', '2': 'outgoing', '3': 'missed', '5': 'rejected'}
                direction = direction_map.get(call_type, f'type_{call_type}')
                
                days[date]['phone_calls'].append({
                    'time': dt.strftime('%H:%M:%S'),
                    'direction': direction,
                    'duration_seconds': duration,
                })
    except Exception as e:
        print(f"  Call log error: {e}")
    
    # Load signal calls
    print("Loading Signal calls...")
    try:
        conn = sqlite3.connect(SIGNAL_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT json FROM messages WHERE type='call-history'")
        for row in cursor:
            data = json.loads(row['json'])
            call_data = data.get('callHistoryDetails', data.get('callHistory', {}))
            ts = data.get('sent_at', data.get('timestamp', 0))
            if ts:
                dt = datetime.fromtimestamp(ts / 1000)
                date = dt.strftime('%Y-%m-%d')
                conv_id = data.get('conversationId', '')
                
                direction = call_data.get('wasIncoming', call_data.get('direction', ''))
                if isinstance(direction, bool):
                    direction = 'incoming' if direction else 'outgoing'
                
                days[date]['signal_calls'].append({
                    'time': dt.strftime('%H:%M:%S'),
                    'direction': str(direction),
                    'event': call_data.get('status', call_data.get('event', '')),
                })
        conn.close()
    except Exception as e:
        print(f"  Signal calls error: {e}")
    
    # Sort messages within each day
    for date in days:
        days[date]['signal_messages'].sort(key=lambda m: m.get('timestamp_ms', 0) or m['time'])
        days[date]['sms_messages'].sort(key=lambda m: m.get('timestamp_ms', 0) or m['time'])
    
    print(f"  Loaded data for {len(days)} days")
    return dict(days)


# ──────────────────────────────────────────────────────────────────────────────
# MONTHLY FILE GENERATION
# ──────────────────────────────────────────────────────────────────────────────

def generate_month_file(month_str, month_days, all_days):
    """Generate a detailed markdown file for one month."""
    
    lines = []
    dt_month = datetime.strptime(month_str + '-01', '%Y-%m-%d')
    month_name = dt_month.strftime('%B %Y')
    
    # Get sorted dates for this month
    sorted_dates = sorted(d for d in month_days.keys())
    if not sorted_dates:
        return None
    
    # ── HEADER ──
    lines.append(f"# {month_name} — Signal Conversation Log\n")
    lines.append(f"**Contact**: {CONTACT_NAME} ({CONTACT_PHONE})")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Legend**: → = You sent | ← = She sent | 📞 = Phone call | 🔒 = Signal call\n")
    
    # ── MONTH SUMMARY ──
    total_signal_sent = sum(sum(1 for m in month_days[d]['signal_messages'] if m['direction']=='sent') for d in sorted_dates)
    total_signal_recv = sum(sum(1 for m in month_days[d]['signal_messages'] if m['direction']=='received') for d in sorted_dates)
    total_sms_sent = sum(sum(1 for m in month_days[d]['sms_messages'] if m['direction']=='sent') for d in sorted_dates)
    total_sms_recv = sum(sum(1 for m in month_days[d]['sms_messages'] if m['direction']=='received') for d in sorted_dates)
    total_calls = sum(len(month_days[d]['phone_calls']) for d in sorted_dates)
    total_talk = sum(sum(c['duration_seconds'] for c in month_days[d]['phone_calls']) for d in sorted_dates)
    
    contact_days = sum(1 for d in sorted_dates if month_days[d]['signal_messages'] or month_days[d]['sms_messages'] or month_days[d]['phone_calls'])
    
    lines.append("## Month Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Contact Days | {contact_days}/{len(sorted_dates)} |")
    lines.append(f"| Signal Messages | {total_signal_sent + total_signal_recv:,} (You: {total_signal_sent:,} / Her: {total_signal_recv:,}) |")
    if total_sms_sent + total_sms_recv > 0:
        lines.append(f"| SMS Messages | {total_sms_sent + total_sms_recv:,} (You: {total_sms_sent:,} / Her: {total_sms_recv:,}) |")
    if total_calls > 0:
        h, m = divmod(total_talk // 60, 60)
        lines.append(f"| Phone Calls | {total_calls} ({h}h {m}m total) |")
    lines.append("")
    
    # Analyze each day
    daily_summaries = []
    weekly_data = defaultdict(list)
    
    argument_initiations = {'you': 0, 'her': 0, 'unclear': 0}
    total_msgs_in_args = 0
    total_msgs_all = 0
    total_banter_msgs = 0
    total_banter_minutes = 0
    you_initiated_evidence = []  # collect context for false-positive review
    her_initiated_evidence = []  # collect context for her false-positive review too
    escalation_persistence_events = []  # times someone kept going 20+ min after de-escalation
    argument_topics_you = Counter()  # what you're upset about across all arguments
    argument_topics_her = Counter()  # what she's upset about across all arguments
    all_topics = Counter()
    all_behaviors_you = Counter()
    all_behaviors_her = Counter()
    
    for date in sorted_dates:
        day_data = month_days[date]
        dt_day = datetime.strptime(date, '%Y-%m-%d')
        weekday = dt_day.strftime('%A')
        week_num = dt_day.isocalendar()[1]
        week_key = f"W{week_num}"
        
        # Merge all messages chronologically
        all_msgs = []
        for m in day_data['signal_messages']:
            all_msgs.append(m)
        for m in day_data['sms_messages']:
            all_msgs.append(m)
        all_msgs.sort(key=lambda x: x.get('timestamp_ms', 0) or x['time'])
        
        if not all_msgs and not day_data['phone_calls'] and not day_data['signal_calls']:
            daily_summaries.append({
                'date': date, 'weekday': weekday, 'mood': 'no_contact',
                'total_msgs': 0, 'sent': 0, 'recv': 0,
                'blocks': [], 'summary_notes': ['No contact'],
                'first_msg_time': '', 'last_msg_time': '',
            })
            weekly_data[week_key].append(daily_summaries[-1])
            continue
        
        # Analyze patterns for each message
        for msg in all_msgs:
            msg['_patterns'] = analyze_message_patterns(msg.get('body', ''), msg['direction'])
            msg['_neg_score'] = score_negativity(msg.get('body', ''))
        
        # Detect argument blocks
        blocks = detect_argument_blocks(all_msgs)
        
        # Detect banter blocks
        banter_blocks = detect_banter_blocks(all_msgs)
        
        # Detect conversation gaps
        gaps = detect_conversation_gaps(all_msgs)
        
        # Classify day mood
        mood = classify_day_mood(all_msgs, blocks)
        
        # Count banter time
        for bb in banter_blocks:
            total_banter_msgs += bb['msg_count']
            total_banter_minutes += bb['duration_minutes']
        
        # Count argument initiations + arguing time
        total_msgs_all += len(all_msgs)
        for block in blocks:
            if block.get('is_argument'):
                arg_msg_count = block['end_idx'] - block['start_idx'] + 1
                total_msgs_in_args += arg_msg_count
                init = block.get('initiator', 'unclear')
                
                # Collect argument topics
                if block.get('argument_topic_you'):
                    for t in block['argument_topic_you'].split(', '):
                        argument_topics_you[t.strip()] += 1
                if block.get('argument_topic_her'):
                    for t in block['argument_topic_her'].split(', '):
                        argument_topics_her[t.strip()] += 1
                
                # Collect escalation persistence events
                if block.get('escalation_after_deesc_minutes', 0) >= 10:
                    who_refused = 'Her' if block['refused_deesc_by'] == 'received' else 'You'
                    who_tried = 'You' if block['refused_deesc_by'] == 'received' else 'Her'
                    escalation_persistence_events.append({
                        'date': date,
                        'who_tried_deesc': who_tried,
                        'who_refused': who_refused,
                        'minutes_after': block['escalation_after_deesc_minutes'],
                        'deesc_msg': block['de_escalation_attempts'][0]['body'] if block['de_escalation_attempts'] else '',
                        'deesc_time': block['de_escalation_attempts'][0]['time'] if block['de_escalation_attempts'] else '',
                    })
                
                # Build evidence context for the trigger
                trigger_idx = block.get('trigger_idx', block['start_idx'])
                context_start = max(0, trigger_idx - 5)
                context_msgs = []
                for ci in range(context_start, min(trigger_idx + 6, len(all_msgs))):
                    m = all_msgs[ci]
                    arrow = '→ YOU' if m['direction'] == 'sent' else '← HER'
                    body = (m.get('body', '') or '')[:150]
                    marker = ' ◀◀ TRIGGER' if ci == trigger_idx else ''
                    hostility = m.get('_hostility', 0)
                    context_msgs.append(f"{m['time']} {arrow}: {body} [h={hostility}]{marker}")
                
                evidence_entry = {
                    'date': date,
                    'time': block.get('trigger_time', ''),
                    'trigger_msg': block.get('trigger_msg', ''),
                    'arg_length': arg_msg_count,
                    'context': context_msgs,
                    'topic_you': block.get('argument_topic_you', ''),
                    'topic_her': block.get('argument_topic_her', ''),
                    'deesc_minutes': block.get('escalation_after_deesc_minutes', 0),
                    'refused_by': 'Her' if block.get('refused_deesc_by') == 'received' else ('You' if block.get('refused_deesc_by') == 'sent' else ''),
                }
                
                if init == 'sent':
                    argument_initiations['you'] += 1
                    you_initiated_evidence.append(evidence_entry)
                elif init == 'received':
                    argument_initiations['her'] += 1
                    her_initiated_evidence.append(evidence_entry)
                else:
                    argument_initiations['unclear'] += 1
        
        # Count topics
        for msg in all_msgs:
            for topic in msg.get('_patterns', {}).get('topics', []):
                all_topics[topic] += 1
        
        # Count behaviors
        for msg in all_msgs:
            pats = msg.get('_patterns', {})
            if msg['direction'] == 'sent':
                for cat in ('passive_aggressive', 'escalation'):
                    for label in pats.get(cat, []):
                        all_behaviors_you[label] += 1
            else:
                for cat in ('passive_aggressive', 'escalation'):
                    for label in pats.get(cat, []):
                        all_behaviors_her[label] += 1
        
        sent = sum(1 for m in all_msgs if m['direction'] == 'sent')
        recv = sum(1 for m in all_msgs if m['direction'] == 'received')
        
        summary = {
            'date': date,
            'weekday': weekday,
            'mood': mood,
            'total_msgs': len(all_msgs),
            'sent': sent,
            'recv': recv,
            'blocks': blocks,
            'gaps': gaps,
            'first_msg_time': all_msgs[0]['time'] if all_msgs else '',
            'last_msg_time': all_msgs[-1]['time'] if all_msgs else '',
            'calls': day_data['phone_calls'],
            'signal_calls': day_data['signal_calls'],
            'summary_notes': [],
            'all_msgs': all_msgs,
        }
        
        # Build summary notes
        arg_blocks = [b for b in blocks if b['is_argument']]
        if arg_blocks:
            for ab in arg_blocks:
                init_who = 'You' if ab.get('initiator') == 'sent' else ('Her' if ab.get('initiator') == 'received' else 'Unclear')
                trigger = ab.get('trigger_msg', '')[:100]
                summary['summary_notes'].append(f"⚡ Argument ({init_who} initiated): \"{trigger}\"")
        
        if mood == 'loving':
            pos_count = sum(1 for m in all_msgs if m.get('_patterns', {}).get('positive'))
            summary['summary_notes'].append(f"💚 Positive day — {pos_count} affectionate messages")
        
        if gaps:
            for gap in gaps:
                summary['summary_notes'].append(f"⏸️ {gap['gap_str']} silence gap")
        
        daily_summaries.append(summary)
        weekly_data[week_key].append(summary)
    
    # ── MONTH BEHAVIOR OVERVIEW ──
    lines.append("## Behavioral Overview\n")
    
    # ── TIME BREAKDOWN: Arguing vs Banter vs Normal ──
    total_args = argument_initiations['you'] + argument_initiations['her'] + argument_initiations['unclear']
    arg_pct = (total_msgs_in_args / total_msgs_all * 100) if total_msgs_all > 0 else 0
    banter_pct = (total_banter_msgs / total_msgs_all * 100) if total_msgs_all > 0 else 0
    normal_msgs = total_msgs_all - total_msgs_in_args - total_banter_msgs
    normal_pct = (normal_msgs / total_msgs_all * 100) if total_msgs_all > 0 else 0
    
    lines.append("### Conversation Breakdown\n")
    lines.append("| Category | Messages | % of Total | Note |")
    lines.append("|----------|----------|------------|------|")
    lines.append(f"| 😊 Joking/Banter | {total_banter_msgs:,} | {banter_pct:.1f}% | Both laughing/playful |")
    lines.append(f"| ⚡ Arguments | {total_msgs_in_args:,} | {arg_pct:.1f}% | Mutual hostility detected |")
    lines.append(f"| 💬 Normal conversation | {normal_msgs:,} | {normal_pct:.1f}% | Everything else |")
    lines.append(f"| **Total** | **{total_msgs_all:,}** | **100%** | {total_args} argument blocks |")
    lines.append("")
    
    lines.append("### Argument Initiation\n")
    lines.append("_Based on who first directed hostility at the other. Excludes: jokes, apologies, self-deprecation, venting about work/third parties._\n")
    lines.append("| Who Started It | Count |")
    lines.append("|----------------|-------|")
    lines.append(f"| You | {argument_initiations['you']} |")
    lines.append(f"| Her | {argument_initiations['her']} |")
    lines.append(f"| Unclear | {argument_initiations['unclear']} |")
    lines.append("")
    
    # ── WHAT EACH PERSON ARGUES ABOUT ──
    if argument_topics_you or argument_topics_her:
        lines.append("### What Each Person Gets Upset About\n")
        lines.append("| Topic | You | Her |")
        lines.append("|-------|-----|-----|")
        all_topic_labels = sorted(set(list(argument_topics_you.keys()) + list(argument_topics_her.keys())))
        for label in all_topic_labels:
            lines.append(f"| {label.title()} | {argument_topics_you.get(label, 0)} | {argument_topics_her.get(label, 0)} |")
        lines.append("")
    
    # ── ESCALATION PERSISTENCE (who keeps going after de-escalation) ──
    if escalation_persistence_events:
        lines.append("### 🔴 Escalation After De-Escalation Attempts\n")
        lines.append("_Times someone continued being hostile 10+ minutes after the other person tried to de-escalate or disengage._\n")
        lines.append("| Date | Who Tried to Stop | Who Kept Going | Minutes After | De-escalation Message |")
        lines.append("|------|-------------------|----------------|---------------|----------------------|")
        for ev in escalation_persistence_events:
            lines.append(f"| {ev['date']} | {ev['who_tried_deesc']} | **{ev['who_refused']}** | **{ev['minutes_after']:.0f} min** | \"{ev['deesc_msg'][:80]}\" |")
        lines.append("")
        
        # Tally
        you_refused = sum(1 for e in escalation_persistence_events if e['who_refused'] == 'You')
        her_refused = sum(1 for e in escalation_persistence_events if e['who_refused'] == 'Her')
        lines.append(f"**Summary**: You refused to de-escalate: {you_refused} times | She refused to de-escalate: **{her_refused} times**\n")
    
    # ── YOUR INITIATIONS — FALSE POSITIVE REVIEW ──
    if you_initiated_evidence:
        lines.append("### ⚠️ YOUR Argument Initiations — Evidence Review\n")
        lines.append("_Each entry shows 5 messages before + after the trigger. h= directed hostility score (0=neutral, 1=mild, 2+=hostile toward partner)._")
        lines.append("_Jokes, apologies, self-deprecation, and third-party venting are already FILTERED OUT._\n")
        for idx, ev in enumerate(you_initiated_evidence, 1):
            topic_str = f" | You upset about: {ev['topic_you']}" if ev['topic_you'] else ""
            deesc_str = f" | {ev['refused_by']} kept going {ev['deesc_minutes']:.0f}min after de-escalation" if ev['deesc_minutes'] >= 10 else ""
            lines.append(f"**#{idx} — {ev['date']} at {ev['time']}** ({ev['arg_length']} msgs){topic_str}{deesc_str}")
            lines.append("```")
            for ctx_line in ev['context']:
                lines.append(ctx_line)
            lines.append("```")
            lines.append("")
        lines.append("---\n")
    
    # ── HER INITIATIONS — FALSE POSITIVE REVIEW ──
    if her_initiated_evidence:
        lines.append("### ⚠️ HER Argument Initiations — Evidence Review\n")
        lines.append("_Same format. Check if she was genuinely starting it or responding to something._\n")
        for idx, ev in enumerate(her_initiated_evidence, 1):
            topic_str = f" | She upset about: {ev['topic_her']}" if ev['topic_her'] else ""
            deesc_str = f" | {ev['refused_by']} kept going {ev['deesc_minutes']:.0f}min after de-escalation" if ev['deesc_minutes'] >= 10 else ""
            lines.append(f"**#{idx} — {ev['date']} at {ev['time']}** ({ev['arg_length']} msgs){topic_str}{deesc_str}")
            lines.append("```")
            for ctx_line in ev['context']:
                lines.append(ctx_line)
            lines.append("```")
            lines.append("")
        lines.append("---\n")
    
    if all_topics:
        lines.append("### Top Conversation Topics\n")
        lines.append("| Topic | Mentions |")
        lines.append("|-------|----------|")
        for topic, count in all_topics.most_common(10):
            lines.append(f"| {topic.replace('_', ' ').title()} | {count} |")
        lines.append("")
    
    if all_behaviors_you or all_behaviors_her:
        lines.append("### Negative Behavior Patterns\n")
        all_labels = sorted(set(list(all_behaviors_you.keys()) + list(all_behaviors_her.keys())))
        if all_labels:
            lines.append("| Pattern | You | Her |")
            lines.append("|---------|-----|-----|")
            for label in all_labels:
                lines.append(f"| {label.replace('_', ' ').title()} | {all_behaviors_you.get(label, 0)} | {all_behaviors_her.get(label, 0)} |")
            lines.append("")
    
    # ── WEEKLY SUMMARIES ──
    lines.append("## Weekly Summaries\n")
    for week_key in sorted(weekly_data.keys()):
        week_days = weekly_data[week_key]
        w_msgs = sum(d['total_msgs'] for d in week_days)
        w_args = sum(sum(1 for b in d.get('blocks', []) if b.get('is_argument')) for d in week_days)
        w_moods = Counter(d['mood'] for d in week_days)
        
        dates_range = f"{week_days[0]['date']} – {week_days[-1]['date']}"
        mood_str = ', '.join(f"{k}: {v}" for k, v in w_moods.most_common())
        
        lines.append(f"### {week_key} ({dates_range})")
        lines.append(f"- **Messages**: {w_msgs:,} | **Arguments**: {w_args} | **Mood**: {mood_str}")
        
        # Week highlights
        for d in week_days:
            if d['summary_notes']:
                for note in d['summary_notes']:
                    if '⚡' in note:
                        lines.append(f"  - {d['date']}: {note}")
        lines.append("")
    
    # ── DAILY LOGS ──
    lines.append("---\n")
    lines.append("## Daily Conversation Logs\n")
    
    for summary in daily_summaries:
        date = summary['date']
        weekday = summary['weekday']
        mood = summary['mood']
        
        mood_emoji = {
            'explosive': '💥', 'heated': '🔴', 'tense': '🟠',
            'loving': '💚', 'neutral': '⚪', 'no_contact': '📵'
        }.get(mood, '⚪')
        
        lines.append(f"### {date} ({weekday}) {mood_emoji} {mood.upper()}")
        
        if mood == 'no_contact':
            lines.append("_No contact this day_\n")
            continue
        
        # Verification line
        lines.append(f"_Msgs: {summary['total_msgs']} ({summary['sent']}↑ {summary['recv']}↓) | First: {summary['first_msg_time']} | Last: {summary['last_msg_time']}_")
        
        # Calls
        if summary.get('calls'):
            call_strs = []
            for c in summary['calls']:
                dur = f" ({c['duration_seconds']}s)" if c['duration_seconds'] > 0 else ""
                call_strs.append(f"📞 {c['time']} {c['direction']}{dur}")
            lines.append(f"_{' · '.join(call_strs)}_")
        
        if summary.get('signal_calls'):
            for c in summary['signal_calls']:
                lines.append(f"_🔒 Signal call {c['time']} {c['direction']} ({c.get('event', '')})")
        
        # Summary notes
        if summary['summary_notes']:
            lines.append("")
            for note in summary['summary_notes']:
                lines.append(f"> {escape_md(note)}")
        
        lines.append("")
        
        # Messages
        all_msgs = summary.get('all_msgs', [])
        if not all_msgs:
            lines.append("_No text messages_\n")
            continue
        
        # Insert gap markers
        gap_dict = {}
        for gap in summary.get('gaps', []):
            gap_dict[gap['after_idx']] = gap['gap_str']
        
        # Mark argument boundaries
        arg_ranges = set()
        for block in summary.get('blocks', []):
            if block.get('is_argument'):
                for idx in range(block['start_idx'], block['end_idx'] + 1):
                    arg_ranges.add(idx)
        
        in_argument = False
        current_arg_block = None
        for i, msg in enumerate(all_msgs):
            # Gap marker
            if i in gap_dict:
                lines.append(f"\n⏸️ _{gap_dict[i]} silence_\n")
            
            # Argument boundary markers
            if i in arg_ranges and not in_argument:
                in_argument = True
                # Find the block this belongs to
                for block in summary.get('blocks', []):
                    if block.get('is_argument') and block['start_idx'] == i:
                        current_arg_block = block
                        init_who = 'You' if block.get('initiator') == 'sent' else ('Her' if block.get('initiator') == 'received' else '?')
                        topic_you = block.get('argument_topic_you', '')
                        topic_her = block.get('argument_topic_her', '')
                        topic_parts = []
                        if topic_you:
                            topic_parts.append(f"You upset about: {topic_you}")
                        if topic_her:
                            topic_parts.append(f"Her upset about: {topic_her}")
                        topic_str = f"\n> 📋 {' | '.join(topic_parts)}" if topic_parts else ""
                        lines.append(f"\n> ⚡ **ARGUMENT START** — Initiated by: **{init_who}**{topic_str}")
                        break
            elif i not in arg_ranges and in_argument:
                in_argument = False
                if current_arg_block and current_arg_block.get('escalation_after_deesc_minutes', 0) >= 10:
                    who_refused = 'Her' if current_arg_block.get('refused_deesc_by') == 'received' else 'You'
                    who_tried = 'You' if current_arg_block.get('refused_deesc_by') == 'received' else 'Her'
                    mins = current_arg_block['escalation_after_deesc_minutes']
                    lines.append(f"> 🔴 **{who_tried} tried to de-escalate → {who_refused} kept going {mins:.0f} more minutes**")
                lines.append("> ✅ **ARGUMENT END**\n")
                current_arg_block = None
            
            # The message itself
            arrow = "→" if msg['direction'] == 'sent' else "←"
            body = msg.get('body', '')
            source_tag = f" `[SMS]`" if msg.get('source') == 'sms' else ""
            
            # Add behavior flags inline
            pats = msg.get('_patterns', {})
            flags = []
            if pats.get('escalation'):
                flags.append(f"⚠️{','.join(pats['escalation'][:2])}")
            if pats.get('passive_aggressive'):
                flags.append(f"😒{','.join(pats['passive_aggressive'][:2])}")
            
            flag_str = f" {' '.join(flags)}" if flags else ""
            
            if body:
                lines.append(f"**{msg['time']}** {arrow} {escape_md(body)}{source_tag}{flag_str}")
            elif msg.get('has_attachments'):
                lines.append(f"**{msg['time']}** {arrow} _[attachment]_{source_tag}")
        
        if in_argument:
            lines.append("> ✅ **ARGUMENT END**\n")
        
        lines.append("")
    
    # ── FOOTNOTES ──
    lines.append("---\n")
    lines.append("## Footnotes & Missing Context\n")
    lines.append("- Phone calls are metadata only — no audio content is available")
    lines.append("- Signal calls show direction and accept/reject status only")
    lines.append("- Attachments (photos, voice notes) are referenced but content not extracted")
    lines.append("- Argument detection is automated — review flagged sections for accuracy")
    lines.append("- 'Initiated by' tracks who sent the first negative-scored message in an argument block")
    lines.append("- Some arguments may start over phone calls and only escalate to text afterward")
    lines.append("")
    lines.append("### Missing Context Flags")
    lines.append("_The following gaps may need manual review:_\n")
    
    for summary in daily_summaries:
        if summary.get('gaps'):
            for gap in summary['gaps']:
                lines.append(f"- **{summary['date']}**: {gap['gap_str']} silence at {summary.get('all_msgs', [{}])[gap['after_idx']]['time'] if gap['after_idx'] < len(summary.get('all_msgs', [])) else '?'} — phone call? in-person meeting?")
    
    lines.append("")
    
    # ── VERIFICATION DATA ──
    lines.append("## Verification Data (Cross-Reference)\n")
    lines.append("_Use these counts to verify against your phone. Pick any date and check message counts match._\n")
    lines.append("| Date | Signal↑ | Signal↓ | SMS↑ | SMS↓ | First Msg | Last Msg |")
    lines.append("|------|---------|---------|------|------|-----------|----------|")
    for summary in daily_summaries:
        if summary['total_msgs'] > 0:
            date = summary['date']
            day_data = month_days.get(date, {})
            sig_sent = sum(1 for m in day_data.get('signal_messages', []) if m['direction'] == 'sent')
            sig_recv = sum(1 for m in day_data.get('signal_messages', []) if m['direction'] == 'received')
            sms_sent = sum(1 for m in day_data.get('sms_messages', []) if m['direction'] == 'sent')
            sms_recv = sum(1 for m in day_data.get('sms_messages', []) if m['direction'] == 'received')
            lines.append(f"| {date} | {sig_sent} | {sig_recv} | {sms_sent} | {sms_recv} | {summary['first_msg_time']} | {summary['last_msg_time']} |")
    lines.append("")
    
    return '\n'.join(lines)


def generate_week_file(month_str, week_key, week_summaries, month_days):
    """Generate a weekly file with word-for-word daily conversation logs."""
    lines = []
    
    if not week_summaries:
        return None
    
    dates = [s['date'] for s in week_summaries]
    dt_month = datetime.strptime(month_str + '-01', '%Y-%m-%d')
    month_name = dt_month.strftime('%B %Y')
    
    lines.append(f"# {month_name} — {week_key} ({dates[0]} to {dates[-1]})\n")
    lines.append(f"**Contact**: {CONTACT_NAME} ({CONTACT_PHONE})")
    lines.append(f"**Legend**: → = You sent | ← = She sent | 📞 = Phone call")
    lines.append(f"**This is a WORD-FOR-WORD log** — every message is exactly as sent.\n")
    
    # Week quick stats
    w_msgs = sum(d['total_msgs'] for d in week_summaries)
    w_sent = sum(d['sent'] for d in week_summaries)
    w_recv = sum(d['recv'] for d in week_summaries)
    w_args = sum(sum(1 for b in d.get('blocks', []) if b.get('is_argument')) for d in week_summaries)
    moods = Counter(d['mood'] for d in week_summaries)
    
    # Arguing + banter time
    w_arg_msgs = 0
    w_banter_msgs = 0
    w_you_starts = []
    w_her_starts = []
    w_escalation_events = []
    
    for d in week_summaries:
        # Banter
        all_day_msgs = d.get('all_msgs', [])
        if all_day_msgs:
            day_banter = detect_banter_blocks(all_day_msgs)
            for bb in day_banter:
                w_banter_msgs += bb['msg_count']
        
        for block in d.get('blocks', []):
            if block.get('is_argument'):
                block_len = block['end_idx'] - block['start_idx'] + 1
                w_arg_msgs += block_len
                
                # Build evidence for trigger
                trigger_idx = block.get('trigger_idx', block['start_idx'])
                ctx_start = max(0, trigger_idx - 5)
                ctx_lines = []
                for ci in range(ctx_start, min(trigger_idx + 6, len(all_day_msgs))):
                    m = all_day_msgs[ci]
                    arrow = '→ YOU' if m['direction'] == 'sent' else '← HER'
                    body = (m.get('body', '') or '')[:150]
                    marker = ' ◀◀ TRIGGER' if ci == trigger_idx else ''
                    hostility = m.get('_hostility', 0)
                    ctx_lines.append(f"{m['time']} {arrow}: {escape_md(body)} [h={hostility}]{marker}")
                
                ev_entry = {
                    'date': d['date'],
                    'time': block.get('trigger_time', ''),
                    'trigger_msg': block.get('trigger_msg', ''),
                    'arg_length': block_len,
                    'context': ctx_lines,
                    'topic_you': block.get('argument_topic_you', ''),
                    'topic_her': block.get('argument_topic_her', ''),
                    'deesc_minutes': block.get('escalation_after_deesc_minutes', 0),
                    'refused_by': 'Her' if block.get('refused_deesc_by') == 'received' else ('You' if block.get('refused_deesc_by') == 'sent' else ''),
                }
                
                if block.get('initiator') == 'sent':
                    w_you_starts.append(ev_entry)
                elif block.get('initiator') == 'received':
                    w_her_starts.append(ev_entry)
                
                # Escalation persistence
                if block.get('escalation_after_deesc_minutes', 0) >= 10:
                    who_refused = 'Her' if block['refused_deesc_by'] == 'received' else 'You'
                    who_tried = 'You' if block['refused_deesc_by'] == 'received' else 'Her'
                    w_escalation_events.append({
                        'date': d['date'],
                        'who_tried': who_tried,
                        'who_refused': who_refused,
                        'minutes': block['escalation_after_deesc_minutes'],
                    })
    
    w_arg_pct = (w_arg_msgs / w_msgs * 100) if w_msgs > 0 else 0
    w_banter_pct = (w_banter_msgs / w_msgs * 100) if w_msgs > 0 else 0
    
    lines.append(f"**Week Total**: {w_msgs:,} msgs ({w_sent:,}↑ {w_recv:,}↓)")
    lines.append(f"**Arguments**: {w_args} blocks ({w_arg_msgs:,} msgs, {w_arg_pct:.1f}%) | **Banter**: {w_banter_msgs:,} msgs ({w_banter_pct:.1f}%)")
    lines.append(f"**Who Started**: You: {len(w_you_starts)} | Her: {len(w_her_starts)}")
    lines.append(f"**Day Moods**: {', '.join(f'{k}:{v}' for k, v in moods.most_common())}\n")
    
    # Highlights
    for d in week_summaries:
        if d['summary_notes']:
            for note in d['summary_notes']:
                if '⚡' in note or '💚' in note:
                    lines.append(f"- **{d['date']}** {note}")
    lines.append("")
    
    # Escalation persistence summary
    if w_escalation_events:
        lines.append("### 🔴 Escalation After De-Escalation\n")
        for ev in w_escalation_events:
            lines.append(f"- **{ev['date']}**: {ev['who_tried']} tried to stop → **{ev['who_refused']} kept going {ev['minutes']:.0f} more minutes**")
        lines.append("")
    
    # Your initiations evidence
    if w_you_starts:
        lines.append(f"### ⚠️ You Started {len(w_you_starts)} Argument(s)\n")
        lines.append("_h= directed hostility score (0=neutral, jokes/apologies/venting filtered out)_\n")
        for idx, ev in enumerate(w_you_starts, 1):
            topic_str = f" | About: {ev['topic_you']}" if ev['topic_you'] else ""
            lines.append(f"**#{idx} — {ev['date']} at {ev['time']}** ({ev['arg_length']} msgs){topic_str}")
            lines.append("```")
            for ctx_line in ev['context']:
                lines.append(ctx_line)
            lines.append("```")
            lines.append("")
    
    # Her initiations evidence
    if w_her_starts:
        lines.append(f"### ⚠️ She Started {len(w_her_starts)} Argument(s)\n")
        for idx, ev in enumerate(w_her_starts, 1):
            topic_str = f" | About: {ev['topic_her']}" if ev['topic_her'] else ""
            deesc_str = f" | **{ev['refused_by']} kept going {ev['deesc_minutes']:.0f}min after de-escalation**" if ev['deesc_minutes'] >= 10 else ""
            lines.append(f"**#{idx} — {ev['date']} at {ev['time']}** ({ev['arg_length']} msgs){topic_str}{deesc_str}")
            lines.append("```")
            for ctx_line in ev['context']:
                lines.append(ctx_line)
            lines.append("```")
            lines.append("")
    
    lines.append("---\n")
    
    # ── DAILY LOGS ──
    for summary in week_summaries:
        date = summary['date']
        weekday = summary['weekday']
        mood = summary['mood']
        
        mood_emoji = {
            'explosive': '💥', 'heated': '🔴', 'tense': '🟠',
            'loving': '💚', 'neutral': '⚪', 'no_contact': '📵'
        }.get(mood, '⚪')
        
        lines.append(f"## {date} ({weekday}) {mood_emoji} {mood.upper()}")
        
        if mood == 'no_contact':
            lines.append("_No contact this day_\n")
            continue
        
        # Verification line
        lines.append(f"_Msgs: {summary['total_msgs']} ({summary['sent']}↑ {summary['recv']}↓) | First: {summary['first_msg_time']} | Last: {summary['last_msg_time']}_")
        
        # Calls
        if summary.get('calls'):
            call_strs = []
            for c in summary['calls']:
                dur = f" ({c['duration_seconds']}s)" if c['duration_seconds'] > 0 else ""
                call_strs.append(f"📞 {c['time']} {c['direction']}{dur}")
            lines.append(f"_{' · '.join(call_strs)}_")
        
        if summary.get('signal_calls'):
            for c in summary['signal_calls']:
                lines.append(f"_🔒 Signal call {c['time']} {c['direction']} ({c.get('event', '')})")
        
        # Summary notes
        if summary['summary_notes']:
            lines.append("")
            for note in summary['summary_notes']:
                lines.append(f"> {escape_md(note)}")
        
        lines.append("")
        
        # Messages
        all_msgs = summary.get('all_msgs', [])
        if not all_msgs:
            lines.append("_No text messages_\n")
            continue
        
        gap_dict = {}
        for gap in summary.get('gaps', []):
            gap_dict[gap['after_idx']] = gap['gap_str']
        
        arg_ranges = set()
        for block in summary.get('blocks', []):
            if block.get('is_argument'):
                for idx in range(block['start_idx'], block['end_idx'] + 1):
                    arg_ranges.add(idx)
        
        in_argument = False
        current_arg_block = None
        for i, msg in enumerate(all_msgs):
            if i in gap_dict:
                lines.append(f"\n⏸️ _{gap_dict[i]} silence_\n")
            
            if i in arg_ranges and not in_argument:
                in_argument = True
                for block in summary.get('blocks', []):
                    if block.get('is_argument') and block['start_idx'] == i:
                        current_arg_block = block
                        init_who = 'You' if block.get('initiator') == 'sent' else ('Her' if block.get('initiator') == 'received' else '?')
                        topic_you = block.get('argument_topic_you', '')
                        topic_her = block.get('argument_topic_her', '')
                        topic_parts = []
                        if topic_you:
                            topic_parts.append(f"You upset about: {topic_you}")
                        if topic_her:
                            topic_parts.append(f"Her upset about: {topic_her}")
                        topic_str = f"\n> 📋 {' | '.join(topic_parts)}" if topic_parts else ""
                        lines.append(f"\n> ⚡ **ARGUMENT START** — Initiated by: **{init_who}**{topic_str}")
                        break
            elif i not in arg_ranges and in_argument:
                in_argument = False
                # Show de-escalation summary at end of argument
                if current_arg_block and current_arg_block.get('escalation_after_deesc_minutes', 0) >= 10:
                    who_refused = 'Her' if current_arg_block.get('refused_deesc_by') == 'received' else 'You'
                    who_tried = 'You' if current_arg_block.get('refused_deesc_by') == 'received' else 'Her'
                    mins = current_arg_block['escalation_after_deesc_minutes']
                    lines.append(f"> 🔴 **{who_tried} tried to de-escalate → {who_refused} kept going {mins:.0f} more minutes**")
                lines.append("> ✅ **ARGUMENT END**\n")
                current_arg_block = None
            
            arrow = "→" if msg['direction'] == 'sent' else "←"
            body = msg.get('body', '')
            source_tag = f" `[SMS]`" if msg.get('source') == 'sms' else ""
            
            pats = msg.get('_patterns', {})
            flags = []
            if pats.get('escalation'):
                flags.append(f"⚠️{','.join(pats['escalation'][:2])}")
            if pats.get('passive_aggressive'):
                flags.append(f"😒{','.join(pats['passive_aggressive'][:2])}")
            
            flag_str = f" {' '.join(flags)}" if flags else ""
            
            if body:
                lines.append(f"**{msg['time']}** {arrow} {escape_md(body)}{source_tag}{flag_str}")
            elif msg.get('has_attachments'):
                lines.append(f"**{msg['time']}** {arrow} _[attachment]_{source_tag}")
        
        if in_argument:
            lines.append("> ✅ **ARGUMENT END**\n")
        
        lines.append("")
    
    # ── VERIFICATION ──
    lines.append("---\n")
    lines.append("## Verification (Cross-Reference)\n")
    lines.append("| Date | Signal↑ | Signal↓ | SMS↑ | SMS↓ | First | Last |")
    lines.append("|------|---------|---------|------|------|-------|------|")
    for summary in week_summaries:
        if summary['total_msgs'] > 0:
            date = summary['date']
            day_data = month_days.get(date, {})
            sig_sent = sum(1 for m in day_data.get('signal_messages', []) if m['direction'] == 'sent')
            sig_recv = sum(1 for m in day_data.get('signal_messages', []) if m['direction'] == 'received')
            sms_sent = sum(1 for m in day_data.get('sms_messages', []) if m['direction'] == 'sent')
            sms_recv = sum(1 for m in day_data.get('sms_messages', []) if m['direction'] == 'received')
            lines.append(f"| {date} | {sig_sent} | {sig_recv} | {sms_sent} | {sms_recv} | {summary['first_msg_time']} | {summary['last_msg_time']} |")
    lines.append("")
    
    return '\n'.join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  MONTHLY CONVERSATION BREAKDOWN — Detailed Analysis")
    print("=" * 70)
    
    # Load all data
    days = load_all_data()
    
    # Group by month
    months = defaultdict(dict)
    for date, day_data in days.items():
        month = date[:7]
        months[month][date] = day_data
    
    print(f"\n📅 Months to process: {len(months)}")
    for month in sorted(months.keys()):
        msg_count = sum(len(months[month][d]['signal_messages']) + len(months[month][d]['sms_messages']) for d in months[month])
        print(f"  {month}: {len(months[month])} days, {msg_count:,} messages")
    
    # Generate each month
    print(f"\n📝 Generating monthly + weekly files...\n")
    
    all_file_info = []  # for index
    
    for month in sorted(months.keys()):
        print(f"  Processing {month}...")
        
        # Create month subfolder
        month_dir = os.path.join(OUTPUT_DIR, month)
        os.makedirs(month_dir, exist_ok=True)
        
        # Generate full month file (summary + behavioral overview — no daily logs)
        content = generate_month_file(month, months[month], days)
        if not content:
            continue
        
        # Strip the daily logs section from the monthly summary to keep it small
        # The monthly file has "## Daily Conversation Logs" section — cut everything after that
        # and replace with links to weekly files
        daily_marker = "## Daily Conversation Logs"
        footnotes_marker = "## Footnotes"
        verification_marker = "## Verification Data"
        
        if daily_marker in content:
            # Extract the parts we want to keep
            before_daily = content[:content.index(daily_marker)]
            
            # Extract footnotes and verification from after daily logs
            footnotes_section = ""
            if footnotes_marker in content:
                footnotes_section = content[content.index(footnotes_marker):]
            elif verification_marker in content:
                footnotes_section = content[content.index(verification_marker):]
            
            # Now we need the daily summaries data to build weekly files
            # Re-parse: we already have it from generate_month_file's internals
            # Instead, generate weekly files from the data directly
            pass
        
        # We need to re-analyze the data to get weekly summaries for the week files
        # Let's do this properly:
        sorted_dates = sorted(months[month].keys())
        
        # Build daily analysis
        daily_summaries = []
        weekly_data = defaultdict(list)
        
        for date in sorted_dates:
            day_data = months[month][date]
            dt_day = datetime.strptime(date, '%Y-%m-%d')
            weekday = dt_day.strftime('%A')
            week_num = dt_day.isocalendar()[1]
            week_key = f"W{week_num}"
            
            all_msgs = list(day_data['signal_messages']) + list(day_data['sms_messages'])
            all_msgs.sort(key=lambda x: x.get('timestamp_ms', 0) or x['time'])
            
            if not all_msgs and not day_data['phone_calls'] and not day_data.get('signal_calls'):
                summary = {
                    'date': date, 'weekday': weekday, 'mood': 'no_contact',
                    'total_msgs': 0, 'sent': 0, 'recv': 0,
                    'blocks': [], 'gaps': [], 'summary_notes': ['No contact'],
                    'first_msg_time': '', 'last_msg_time': '',
                    'calls': day_data['phone_calls'],
                    'signal_calls': day_data.get('signal_calls', []),
                    'all_msgs': [],
                }
                daily_summaries.append(summary)
                weekly_data[week_key].append(summary)
                continue
            
            for msg in all_msgs:
                msg['_patterns'] = analyze_message_patterns(msg.get('body', ''), msg['direction'])
                msg['_neg_score'] = score_negativity(msg.get('body', ''))
            
            blocks = detect_argument_blocks(all_msgs)
            gaps_list = detect_conversation_gaps(all_msgs)
            mood = classify_day_mood(all_msgs, blocks)
            
            sent = sum(1 for m in all_msgs if m['direction'] == 'sent')
            recv = sum(1 for m in all_msgs if m['direction'] == 'received')
            
            summary = {
                'date': date, 'weekday': weekday, 'mood': mood,
                'total_msgs': len(all_msgs), 'sent': sent, 'recv': recv,
                'blocks': blocks, 'gaps': gaps_list,
                'first_msg_time': all_msgs[0]['time'] if all_msgs else '',
                'last_msg_time': all_msgs[-1]['time'] if all_msgs else '',
                'calls': day_data['phone_calls'],
                'signal_calls': day_data.get('signal_calls', []),
                'summary_notes': [],
                'all_msgs': all_msgs,
            }
            
            arg_blocks = [b for b in blocks if b.get('is_argument')]
            for ab in arg_blocks:
                init_who = 'You' if ab.get('initiator') == 'sent' else ('Her' if ab.get('initiator') == 'received' else 'Unclear')
                trigger = ab.get('trigger_msg', '')[:100]
                summary['summary_notes'].append(f"⚡ Argument ({init_who} initiated): \"{trigger}\"")
            
            if mood == 'loving':
                pos_count = sum(1 for m in all_msgs if m.get('_patterns', {}).get('positive'))
                summary['summary_notes'].append(f"💚 Positive day — {pos_count} affectionate messages")
            
            for gap in gaps_list:
                summary['summary_notes'].append(f"⏸️ {gap['gap_str']} silence gap")
            
            daily_summaries.append(summary)
            weekly_data[week_key].append(summary)
        
        # Generate weekly conversation files
        week_files = []
        for week_key in sorted(weekly_data.keys()):
            week_content = generate_week_file(month, week_key, weekly_data[week_key], months[month])
            if week_content:
                size_kb = len(week_content.encode('utf-8')) / 1024
                w_msgs = sum(d['total_msgs'] for d in weekly_data[week_key])
                
                MAX_SIZE_KB = 200
                
                if size_kb <= MAX_SIZE_KB:
                    # Write as single file
                    week_filename = f"{month}-{week_key}.md"
                    week_path = os.path.join(month_dir, week_filename)
                    with open(week_path, 'w', encoding='utf-8') as f:
                        f.write(week_content)
                    week_files.append({
                        'filename': week_filename,
                        'week_key': week_key,
                        'size_kb': size_kb,
                        'msg_count': w_msgs,
                        'dates': f"{weekly_data[week_key][0]['date']} – {weekly_data[week_key][-1]['date']}",
                    })
                    print(f"    📄 {week_filename} ({size_kb:.0f} KB, {w_msgs:,} msgs)")
                else:
                    # Split into per-day files
                    print(f"    ⚠️ {week_key} too large ({size_kb:.0f} KB), splitting by day...")
                    for day_summary in weekly_data[week_key]:
                        day_content = generate_week_file(month, week_key, [day_summary], months[month])
                        if day_content:
                            day_filename = f"{day_summary['date']}.md"
                            day_path = os.path.join(month_dir, day_filename)
                            with open(day_path, 'w', encoding='utf-8') as f:
                                f.write(day_content)
                            day_size_kb = len(day_content.encode('utf-8')) / 1024
                            week_files.append({
                                'filename': day_filename,
                                'week_key': f"{week_key}/{day_summary['date']}",
                                'size_kb': day_size_kb,
                                'msg_count': day_summary['total_msgs'],
                                'dates': day_summary['date'],
                            })
                            print(f"      📄 {day_filename} ({day_size_kb:.0f} KB, {day_summary['total_msgs']:,} msgs)")
        
        # Now write the monthly summary (without daily logs, with links to weekly files)
        if daily_marker in content:
            summary_content = content[:content.index(daily_marker)]
        else:
            summary_content = content
        
        # Add week file links
        summary_content += "## Weekly Files\n\n"
        summary_content += "_Open each week's file for the full daily conversation logs:_\n\n"
        summary_content += "| Week | Dates | Messages | Size |\n"
        summary_content += "|------|-------|----------|------|\n"
        for wf in week_files:
            summary_content += f"| [{wf['week_key']}]({wf['filename']}) | {wf['dates']} | {wf['msg_count']:,} | {wf['size_kb']:.0f} KB |\n"
        summary_content += "\n"
        
        # Add verification data
        summary_content += "## Verification Data (Cross-Reference)\n\n"
        summary_content += "_Use these counts to verify against your phone._\n\n"
        summary_content += "| Date | Signal↑ | Signal↓ | SMS↑ | SMS↓ | First | Last |\n"
        summary_content += "|------|---------|---------|------|------|-------|------|\n"
        for s in daily_summaries:
            if s['total_msgs'] > 0:
                date = s['date']
                dd = months[month].get(date, {})
                sig_s = sum(1 for m in dd.get('signal_messages', []) if m['direction'] == 'sent')
                sig_r = sum(1 for m in dd.get('signal_messages', []) if m['direction'] == 'received')
                sms_s = sum(1 for m in dd.get('sms_messages', []) if m['direction'] == 'sent')
                sms_r = sum(1 for m in dd.get('sms_messages', []) if m['direction'] == 'received')
                summary_content += f"| {date} | {sig_s} | {sig_r} | {sms_s} | {sms_r} | {s['first_msg_time']} | {s['last_msg_time']} |\n"
        summary_content += "\n"
        
        # Write the monthly summary
        summary_path = os.path.join(month_dir, f"{month}-SUMMARY.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        summary_size = len(summary_content.encode('utf-8')) / 1024
        print(f"    📊 {month}-SUMMARY.md ({summary_size:.0f} KB)")
        
        month_msg_count = sum(len(months[month][d]['signal_messages']) + len(months[month][d]['sms_messages']) for d in months[month])
        all_file_info.append({
            'month': month,
            'msg_count': month_msg_count,
            'day_count': len(sorted_dates),
            'week_files': week_files,
            'summary_size_kb': summary_size,
        })
    
    # Generate master index
    print(f"\n📝 Generating master index...")
    index_lines = []
    index_lines.append("# Monthly Conversation Index\n")
    index_lines.append(f"**Contact**: {CONTACT_NAME} ({CONTACT_PHONE})")
    index_lines.append(f"**Total Messages**: ~202,500")
    index_lines.append(f"**Date Range**: October 2024 – February 2026")
    index_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    index_lines.append("## How to Use\n")
    index_lines.append("1. Start with a month's SUMMARY file for behavioral overview")
    index_lines.append("2. Open individual week files to see full conversations")
    index_lines.append("3. Use verification tables to cross-check against phone data")
    index_lines.append("4. Argument blocks are marked with ⚡ START / ✅ END with initiator noted")
    index_lines.append("5. Behavior flags: ⚠️ escalation, 😒 passive-aggressive\n")
    index_lines.append("## Monthly Summaries\n")
    index_lines.append("| Month | Messages | Days | Summary | Weekly Files |")
    index_lines.append("|-------|----------|------|---------|-------------|")
    
    for info in all_file_info:
        m = info['month']
        weeks_str = ', '.join(f"[{wf['week_key']}]({m}/{wf['filename']})" for wf in info['week_files'])
        index_lines.append(f"| [{m}]({m}/{m}-SUMMARY.md) | {info['msg_count']:,} | {info['day_count']} | {info['summary_size_kb']:.0f} KB | {weeks_str} |")
    
    index_lines.append("")
    
    with open(os.path.join(OUTPUT_DIR, "INDEX.md"), 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))
    print(f"    ✅ INDEX.md")
    
    print(f"\n{'=' * 70}")
    print(f"  ✅ ALL FILES SAVED TO: {OUTPUT_DIR}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate monthly conversation breakdown reports')
    parser.add_argument('--config', required=True, help='Path to config.json')
    cli_args = parser.parse_args()

    with open(cli_args.config, 'r', encoding='utf-8') as _f:
        # Config files should be small — reject anything over 10MB
        _f.seek(0, 2)
        if _f.tell() > 10 * 1024 * 1024:
            raise RuntimeError("Config file exceeds 10MB limit")
        _f.seek(0)
        _cfg = json.load(_f)
    SIGNAL_DESKTOP_JSON = _cfg.get("signal_desktop_json", "")
    SMS_XML = _cfg.get("sms_xml", "")
    CALLS_XML = _cfg.get("calls_xml", "")
    SIGNAL_DB = _cfg.get("signal_db", "")
    OUTPUT_DIR = os.path.join(_cfg.get("output_dir", "./output"), "months")
    CONTACT_PHONE = _cfg.get("contact_phone", "")
    PHONE_SUFFIX = _cfg.get("phone_suffix", "")
    CONTACT_NAME = _cfg.get("contact_label", "Contact")
    USER_NAME = _cfg.get("user_label", "User")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    main()
