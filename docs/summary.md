# Part 1: Project Summary

## What It Does

The **Communication Analysis Toolkit** is a research-informed forensic engine designed to analyze text-based communication (SMS, Signal, etc.) for behavioral patterns. It provides objective, data-driven insights into relationship dynamics, specifically detecting clinical patterns associated with high-conflict or manipulative interactions.

### Key Outputs
*   **TIMELINE.md**: A day-by-day narrative of the relationship, flagging specific incidents.
*   **ANALYSIS.md**: Comprehensive statistics including message volume, response times, and pattern breakdowns.
*   **EVIDENCE.md**: A catalog of every flagged message with its severity rating and clinical classification.
*   **DATA.json**: A machine-readable dataset of the entire analysis.

---

## Pattern Detection Categories

The engine uses regex-based detection grounded in peer-reviewed behavioral science.

### 🚩 Core Manipulation (DARVO)
*   **Deny**: Denying events that occurred.
*   **Attack**: Attacking the accuser to deflect blame.
*   **Reverse Victim & Offender**: Claiming victimhood when being the aggressor.
*(Source: Freyd, 1997)*

### 🚩 The "Four Horsemen"
*   **Criticism**: Attacking character rather than behavior.
*   **Contempt**: Expressions of superiority, mockery, or disgust.
*   **Defensiveness**: Counter-blaming or playing the victim.
*   **Stonewalling**: Withdrawal and refusal to engage.
*(Source: Gottman & Silver, 1999)*

### 🚩 Coercive Control
*   **Isolation**: Controlling who the person sees or talks to.
*   **Financial Control**: Using money as leverage.
*   **Weaponizing Health**: Using illness or trauma to manipulate.
*(Source: Stark, 2007)*

### 💛 Positive Communication (New in v3.1)
*   **Validation**: Acknowledging the other person's reality.
*   **Empathy**: Expressing understanding of feelings.
*   **Appreciation**: Expressing gratitude or value.
*   **Responsibility**: Owning one's own actions.

---

## Context-Aware Filtering
To reduce false positives, the system understands context. It suppression negative flags when it detects:
*   ✅ **Apologies** ("I'm sorry", "My bad")
*   ✅ **Self-Directed Negativity** ("I hate myself", not "I hate you")
*   ✅ **De-escalation** ("Let's take a break", "I don't want to fight")
*   ✅ **Banter/Jokes** (Detected via laughter, emojis, and reciprocal tone)
