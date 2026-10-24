# ticket-triage-ai

Paste a support ticket, get a triage result: category, urgency,
confidence, and a suggested reply draft. Triaged tickets join a review
queue where they can be filtered by urgency, category, or status and
marked resolved. Everything runs locally — no ticket text is uploaded,
and nothing is stored beyond the sample fixtures.

I built this to show how a rule-based triage pipeline works end to end:
keyword scoring, urgency signals, confidence as a share of matched
weight, and a human-review flag for the cases automation should not
decide alone.

## How it works

1. **Classification** (`classifier.py`) — weighted keyword lexicons for
   four categories (Billing, Technical, Account, Feature request).
   Confidence is the winning category's share of all matched keyword
   weight; with no matches the ticket becomes "General inquiry" at 35%
   confidence and is flagged for review.
2. **Urgency** — signal words drive it: outage/breach/data-loss signals
   mean Critical, urgent/blocking signals mean High, and so on. A
   feature request is never urgent, whatever words surround it.
3. **Human-review flag** — set when confidence is below 55% or urgency
   is Critical. Those tickets sit at the top of the review queue.
4. **Suggested reply** (`drafts.py`) — one template per category, with
   the opening line adjusted for urgency. It is a draft for a human
   agent, not an auto-reply.
5. **Review queue** — seeded with the six sample tickets; every ticket
   you triage joins it. Filter it, and mark tickets resolved.

There is also a JSON API (`POST /api/triage` with `subject` and `body`).

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 — or click **Load a sample ticket** to
try it with the included fixtures in `samples/` (six fictional support
tickets). The review queue lives at `/queue`.

## Example output

Running the six sample tickets through the classifier produces:

- **Charged twice for my subscription this month** — Billing / Low /
  100% confidence / no review needed
- **App crashes every time I upload a photo** — Technical / Medium /
  100% / no review needed
- **Locked out of my account** — Account / High / 100% / no review
  needed
- **Whole team hit by outage** — Technical / Critical / 100% / needs
  human review
- **Dark mode suggestion** — Feature request / Low / 100% / no review
  needed
- **Invoice shows the wrong price** — Billing / Low / 100% / no review
  needed

A regression test (`test_sample_tickets_cover_each_category`) re-runs
the queue fixtures and asserts all four categories and a Critical
ticket are present.

## Honest limitations

- Classification is literal keyword matching — it will not understand
  paraphrases ("I can't get into my account" without the word "login"
  still matches here, but subtler wording may not).
- Confidence is relative to the static lexicon, not a calibrated
  probability — use it to rank tickets, not as a guarantee.
- The review queue lives in memory: restarting the app resets it to
  the six samples. That is deliberate for a demo; a production version
  would persist it in a database.

## Run the tests

```bash
pip install -r requirements.txt
python -m pytest
```
