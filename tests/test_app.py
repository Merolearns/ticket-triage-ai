"""Tests for the Flask app and JSON API."""

import app as app_module


def _client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_home_page_loads():
    response = _client().get("/")
    assert response.status_code == 200
    assert b"Ticket Triage" in response.data


def test_submit_ticket_shows_result_and_joins_queue():
    client = _client()
    before = len(app_module.QUEUE)
    response = client.post("/", data={
        "subject": "Test refund ticket",
        "body": "I was charged twice and need a refund for the duplicate charge.",
    })
    assert response.status_code == 200
    assert b"Billing" in response.data
    assert b"Suggested reply" in response.data
    assert len(app_module.QUEUE) == before + 1


def test_queue_page_loads_and_filters():
    client = _client()
    assert client.get("/queue").status_code == 200
    response = client.get("/queue?urgency=Critical")
    assert response.status_code == 200
    assert b"Critical" in response.data


def test_resolve_marks_ticket_resolved():
    client = _client()
    ticket_id = app_module.QUEUE[0]["id"]
    response = client.post(f"/queue/{ticket_id}/resolve")
    assert response.status_code in (200, 302)
    assert app_module.QUEUE[0]["status"] == "Resolved"
    app_module.QUEUE[0]["status"] = "Open"  # leave the queue as found


def test_api_triage():
    response = _client().post("/api/triage", json={
        "subject": "App crashes on upload",
        "body": "The app crashes and shows an error every time I upload.",
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["category"] == "Technical"
    assert "draft" in data


def test_api_requires_subject_and_body():
    response = _client().post("/api/triage", json={"subject": ""})
    assert response.status_code == 400
