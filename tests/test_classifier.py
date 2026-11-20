"""Tests for the rule-based classifier."""

from classifier import classify


def test_billing_ticket():
    result = classify("Charged twice for my subscription",
                      "I was charged twice and need a refund for the duplicate charge.")
    assert result["category"] == "Billing"
    # No urgency words in this ticket, so it stays low urgency.
    assert result["urgency"] == "Low"
    assert result["confidence"] >= 0.5


def test_service_down_is_not_low():
    # A down service used to triage as Low: "down" matched no urgency signal.
    result = classify("App is down",
                      "The dashboard is down since this morning, nobody can get in.")
    assert result["category"] == "Technical"
    assert result["urgency"] == "Medium"
    assert "down" in result["urgency_signals"]


def test_service_down_plus_blocking_is_high():
    result = classify("App is down",
                      "The app is down and this is blocking my work.")
    assert result["urgency"] == "High"


def test_not_down_stays_low():
    result = classify("Checking status",
                      "Just confirming the app is not down for me.")
    assert result["urgency"] == "Low"


def test_outage_is_critical():
    result = classify("Whole team hit by outage",
                      "There is an outage, the service is down for everyone, urgent.")
    assert result["category"] == "Technical"
    assert result["urgency"] == "Critical"
    assert result["needs_review"] is True


def test_feature_request_is_never_urgent():
    result = classify("Dark mode suggestion",
                      "It would be nice to have dark mode, just a suggestion, urgent please.")
    assert result["category"] == "Feature request"
    assert result["urgency"] == "Low"


def test_plain_question_lists_no_urgency_signals():
    # "question" and "how do i" used to sit in URGENCY_SIGNALS at weight 0:
    # they added nothing to the score but still showed up as urgency
    # signals, so a plain question looked like it carried urgency.
    result = classify("Question about my invoice",
                      "Just a question — how do I download my receipt?")
    assert result["urgency"] == "Low"
    assert result["urgency_signals"] == []


def test_negated_urgency_stays_low():
    result = classify("Plan change",
                      "Just wondering, this is not urgent at all and there is no rush.")
    assert result["urgency"] == "Low"
    assert result["urgency_signals"] == []


def test_negated_urgency_variants_stay_low():
    for body in (
        "This is not really urgent, take your time.",
        "This isn't urgent at all.",
        "Never urgent, no rush on this one.",
    ):
        result = classify("Question", body)
        assert result["urgency"] == "Low"
        assert "urgent" not in result["urgency_signals"]


def test_urgency_still_counts_past_a_negation():
    result = classify("Still broken",
                      "Not urgent for me, but it is urgent for my whole team.")
    assert "urgent" in result["urgency_signals"]
    assert result["urgency"] == "Medium"


def test_negated_category_keyword_does_not_score():
    # "refund" and "login" both weigh 3, so without negation this ties
    # and Billing wins by dict order — but the writer ruled a refund out.
    result = classify("Question",
                      "No refund needed, just a question about my login.")
    assert result["category"] == "Account"
    assert result["category_scores"]["Billing"] == 0
    assert "refund" not in result["matched_keywords"]


def test_unnegated_category_keyword_still_scores():
    result = classify("Refund please", "I need a refund for this charge.")
    assert result["category"] == "Billing"
    assert result["category_scores"]["Billing"] >= 3


def test_locked_out_account_ticket():
    result = classify("Locked out of my account",
                      "I am locked out and cannot log in, the password reset never arrives.")
    assert result["category"] == "Account"


def test_unknown_text_becomes_general_inquiry_and_needs_review():
    result = classify("Hello", "Just saying hello and wondering about things.")
    assert result["category"] == "General inquiry"
    assert result["needs_review"] is True


def test_confidence_is_winning_share():
    result = classify("Refund please",
                      "I need a refund for this charge on my card.")
    assert 0 < result["confidence"] <= 1.0
    assert result["matched_keywords"]


def test_sample_tickets_cover_each_category():
    from app import QUEUE
    categories = {t["category"] for t in QUEUE}
    assert {"Billing", "Technical", "Account", "Feature request"} <= categories
    urgencies = {t["urgency"] for t in QUEUE}
    assert "Critical" in urgencies
