"""Tests for the rule-based classifier."""

from classifier import classify


def test_billing_ticket():
    result = classify("Charged twice for my subscription",
                      "I was charged twice and need a refund for the duplicate charge.")
    assert result["category"] == "Billing"
    # No urgency words in this ticket, so it stays low urgency.
    assert result["urgency"] == "Low"
    assert result["confidence"] >= 0.5


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
