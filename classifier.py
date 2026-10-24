"""Rule-based ticket triage.

Every result is computed from the ticket text itself: category keywords
are weighted, urgency comes from signal words, and confidence is the
winning category's share of all matched keyword weight. Nothing here
calls an external model, so results are fully reproducible.
"""

import re

CATEGORIES = {
    "Billing": {
        "charge": 3, "charged": 3, "refund": 3, "invoice": 3, "billing": 3,
        "payment": 2, "subscription": 2, "price": 2, "card": 2,
        "double charged": 4, "overcharged": 4, "receipt": 2, "coupon": 1,
        "discount": 1, "renewal": 2, "cancel subscription": 3,
    },
    "Technical": {
        "crash": 3, "crashes": 3, "error": 3, "bug": 3, "broken": 3,
        "slow": 2, "loading": 2, "not working": 3, "fails": 2,
        "timeout": 3, "freeze": 3, "freezes": 3, "glitch": 2,
        "upload": 1, "sync": 1, "connection": 1, "offline": 2,
        "outage": 3, "down": 2,
    },
    "Account": {
        "login": 3, "log in": 3, "password": 3, "locked out": 4,
        "account": 2, "sign in": 3, "reset": 2, "two-factor": 3,
        "verification": 2, "access": 2, "username": 2, "email change": 2,
    },
    "Feature request": {
        "feature": 3, "add": 1, "suggest": 3, "suggestion": 3,
        "would be nice": 3, "improve": 2, "wish": 2, "missing feature": 3,
        "support for": 1, "dark mode": 3, "export": 1,
    },
}

# Weight 6 signals jump straight to critical; weight 2 signals push toward
# high; weight 1 signals are ordinary complaints.
URGENCY_SIGNALS = {
    "outage": 6, "down for everyone": 6, "data loss": 6, "breach": 6,
    "hacked": 6, "security": 6, "production down": 6, "all users": 6,
    "urgent": 2, "asap": 2, "immediately": 2, "blocking": 2,
    "can't work": 2, "payment failed": 2, "locked out": 2,
    "losing money": 2, "deadline": 2, "angry": 1, "frustrated": 1,
    "disappointed": 1, "slow": 1, "confused": 1, "question": 0,
    "how do i": 0,
}

REVIEW_CONFIDENCE = 0.55


def _count(text, phrase):
    return len(re.findall(r"\b" + re.escape(phrase) + r"\b", text))


def classify(subject, body):
    """Return a dict with category, urgency, confidence, signals, and flags."""
    text = (subject + " " + body).lower()

    scores = {}
    matched = {}
    for category, keywords in CATEGORIES.items():
        total = 0
        hits = []
        for phrase, weight in keywords.items():
            n = _count(text, phrase)
            if n:
                total += weight * n
                hits.append(phrase)
        scores[category] = total
        matched[category] = hits

    total_score = sum(scores.values())
    if total_score == 0:
        category = "General inquiry"
        confidence = 0.35
        top_hits = []
    else:
        category = max(scores, key=scores.get)
        confidence = round(scores[category] / total_score, 2)
        top_hits = matched[category]

    urgency_hits = []
    urgency_score = 0
    for phrase, weight in URGENCY_SIGNALS.items():
        if _count(text, phrase):
            urgency_hits.append(phrase)
            urgency_score += weight
    if urgency_score >= 6:
        urgency = "Critical"
    elif urgency_score >= 3:
        urgency = "High"
    elif urgency_score >= 1:
        urgency = "Medium"
    else:
        urgency = "Low"

    # A feature request is never urgent, whatever words surround it.
    if category == "Feature request":
        urgency = "Low"

    needs_review = confidence < REVIEW_CONFIDENCE or urgency == "Critical"

    return {
        "category": category,
        "urgency": urgency,
        "confidence": confidence,
        "category_scores": scores,
        "matched_keywords": top_hits,
        "urgency_signals": urgency_hits,
        "needs_review": needs_review,
    }
