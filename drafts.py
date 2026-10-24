"""Suggested reply drafts, one template per category.

The draft is a starting point for a human agent, not an auto-reply: it
names the issue, states the next step, and asks for the one detail most
often missing for that category. Urgency changes the opening line only.
"""

OPENINGS = {
    "Critical": "Thanks for flagging this so quickly — we're treating it as urgent.",
    "High": "Thanks for writing in — we're picking this up as a priority.",
    "Medium": "Thanks for getting in touch.",
    "Low": "Thanks for writing in.",
}

BODIES = {
    "Billing": (
        "I can look into the billing issue on your account right away. "
        "Could you share the last four digits of the card used and the date "
        "of the charge, so I can pull up the exact transaction?"
    ),
    "Technical": (
        "Sorry you're hitting this problem. Could you let me know which "
        "device and browser (or app version) you're on, and the steps that "
        "trigger it? That will help us reproduce it here."
    ),
    "Account": (
        "I can help you get back into your account. Have you tried the "
        "password reset link, and if so, did the reset email arrive? "
        "Let me know and I'll take it from there."
    ),
    "Feature request": (
        "Thanks for the suggestion — this is exactly the kind of feedback "
        "that shapes what we build next. I've passed it to the product team "
        "and noted your account so we can follow up if it ships."
    ),
    "General inquiry": (
        "Happy to help with this. Could you share a little more detail about "
        "what you're trying to do, so I can point you to the right answer?"
    ),
}


def draft_reply(subject, category, urgency):
    opening = OPENINGS.get(urgency, OPENINGS["Medium"])
    body = BODIES.get(category, BODIES["General inquiry"])
    return (
        f"Hi there,\n\n{opening} "
        f"Regarding \"{subject.strip()}\": {body}\n\n"
        "Thanks again for reaching out,\nSupport team"
    )
