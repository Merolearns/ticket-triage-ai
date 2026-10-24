"""Ticket Triage AI — paste a support ticket, get a triage result.

A ticket is classified by category and urgency, given a confidence
score, and paired with a suggested reply draft. Triaged tickets join a
review queue (seeded with samples) where they can be filtered and
marked resolved. Everything runs locally; no ticket text leaves the
machine and nothing is stored on disk beyond the sample fixtures.
"""

import json
import os

from flask import Flask, jsonify, redirect, render_template, request, url_for

from classifier import classify
from drafts import draft_reply

app = Flask(__name__)

SAMPLES_PATH = os.path.join(os.path.dirname(__file__), "samples",
                             "sample_tickets.json")


def _load_queue():
    with open(SAMPLES_PATH, encoding="utf-8") as f:
        tickets = json.load(f)
    queue = []
    for i, ticket in enumerate(tickets, start=1):
        result = classify(ticket["subject"], ticket["body"])
        queue.append({"id": i, "status": "Open", **ticket, **result})
    return queue


QUEUE = _load_queue()
NEXT_ID = len(QUEUE) + 1


def triage_ticket(subject, body):
    result = classify(subject, body)
    result["draft"] = draft_reply(subject, result["category"],
                                  result["urgency"])
    return result


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    subject = ""
    body = ""
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()
        if subject and body:
            result = triage_ticket(subject, body)
            global NEXT_ID
            QUEUE.insert(0, {"id": NEXT_ID, "status": "Open",
                             "subject": subject, "body": body, **result})
            NEXT_ID += 1
    samples = []
    with open(SAMPLES_PATH, encoding="utf-8") as f:
        samples = json.load(f)
    return render_template("index.html", result=result, subject=subject,
                           body=body, samples=samples,
                           queue_count=len(QUEUE))


@app.route("/queue")
def queue():
    urgency = request.args.get("urgency", "")
    category = request.args.get("category", "")
    status = request.args.get("status", "")
    tickets = QUEUE
    if urgency:
        tickets = [t for t in tickets if t["urgency"] == urgency]
    if category:
        tickets = [t for t in tickets if t["category"] == category]
    if status:
        tickets = [t for t in tickets if t["status"] == status]
    counts = {
        "open": sum(1 for t in QUEUE if t["status"] == "Open"),
        "needs_review": sum(1 for t in QUEUE
                            if t["status"] == "Open" and t["needs_review"]),
        "critical": sum(1 for t in QUEUE
                        if t["status"] == "Open" and t["urgency"] == "Critical"),
        "resolved": sum(1 for t in QUEUE if t["status"] == "Resolved"),
    }
    categories = sorted({t["category"] for t in QUEUE})
    return render_template("queue.html", tickets=tickets, counts=counts,
                           categories=categories, urgency=urgency,
                           category=category, status=status)


@app.route("/queue/<int:ticket_id>/resolve", methods=["POST"])
def resolve(ticket_id):
    for ticket in QUEUE:
        if ticket["id"] == ticket_id:
            ticket["status"] = "Resolved"
            break
    return redirect(url_for("queue"))


@app.route("/api/triage", methods=["POST"])
def api_triage():
    data = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    body = (data.get("body") or "").strip()
    if not subject or not body:
        return jsonify({"error": "subject and body are required"}), 400
    return jsonify(triage_ticket(subject, body))


if __name__ == "__main__":
    app.run(debug=True)
