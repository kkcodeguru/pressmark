from datetime import date, timedelta

from app.forms import parse_job


def csrf(client):
    response = client.get("/")
    assert response.status_code == 200
    with client.session_transaction() as sess:
        return sess["csrf_token"]


def job_form(**overrides):
    data = {
        "client": "Adler & Pine",
        "title": "Winter wedding suite",
        "kind": "invitation",
        "quantity": "150",
        "ink": "Bone black",
        "status": "queued",
        "due_on": "2026-10-12",
        "notes": "Belly band in copper.",
    }
    data.update(overrides)
    return data


def create_job(http, **overrides):
    data = job_form(**overrides)
    data["csrf_token"] = csrf(http)
    return http.post("/jobs", data=data)


def test_empty_board(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"No jobs on the board" in response.data


def test_create_show_and_escape(client):
    response = create_job(client, title="<script>alert(1)</script>")
    assert response.status_code == 302
    page = client.get(response.headers["Location"])
    assert page.status_code == 200
    assert b"Job added to the board." in page.data
    assert b"&lt;script&gt;alert(1)&lt;/script&gt;" in page.data
    assert b"<script>alert(1)</script>" not in page.data


def test_validation_errors_keep_the_form(client):
    token = csrf(client)
    response = client.post("/jobs", data=job_form(csrf_token=token, client="", quantity="0"))
    assert response.status_code == 400
    assert b"Client name is required." in response.data
    assert b"Quantity must be between 1 and 100,000." in response.data
    follow = client.get("/")
    assert b"No jobs on the board" in follow.data


def test_parse_job_rejects_a_bad_date():
    _data, errors = parse_job(job_form(due_on="yesterday"))
    assert errors["due_on"] == "Use a valid date."


def test_search_and_filter(client):
    create_job(client, client="Harbor & Rye", title="Bar menu", status="drying", ink="Indigo")
    create_job(client, client="June Calder", title="Calling cards", status="delivered")

    search = client.get("/?q=Harbor")
    assert b"Bar menu" in search.data
    assert b"Calling cards" not in search.data

    filtered = client.get("/?status=delivered")
    assert b"Calling cards" in filtered.data
    assert b"Bar menu" not in filtered.data

    missed = client.get("/?q=no-such-client")
    assert b"Nothing matches" in missed.data

    ignored = client.get("/?status=not-a-status")
    assert b"Bar menu" in ignored.data
    assert b"Calling cards" in ignored.data


def test_edit_status_and_delete(client):
    created = create_job(client, due_on=(date.today() - timedelta(days=1)).isoformat())
    location = created.headers["Location"]
    detail = client.get(location)
    assert b"Overdue" in detail.data

    token = csrf(client)
    updated = client.post(
        location,
        data=job_form(csrf_token=token, title="Spring wedding suite"),
        follow_redirects=True,
    )
    assert b"Job updated." in updated.data
    assert b"Spring wedding suite" in updated.data

    moved = client.post(
        location + "/status",
        data={"csrf_token": token, "status": "on_press"},
        follow_redirects=True,
    )
    assert b"Moved to On press." in moved.data

    removed = client.post(
        location + "/delete",
        data={"csrf_token": token},
        follow_redirects=True,
    )
    assert b"Job removed from the board." in removed.data
    assert b"No jobs on the board" in removed.data


def test_missing_job_and_bad_csrf(client):
    missing = client.get("/jobs/9999")
    assert missing.status_code == 404
    assert b"That docket is not on the board." in missing.data

    token = csrf(client)
    rejected = client.post("/jobs", data=job_form(csrf_token="not-the-token"))
    assert rejected.status_code == 400
    assert b"That form could not be saved." in rejected.data
    assert token != "not-the-token"
