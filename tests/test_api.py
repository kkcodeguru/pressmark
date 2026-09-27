def create_via_api(http, **overrides):
    body = {
        "client": "Harbor & Rye",
        "title": "Bar menu",
        "kind": "menu",
        "quantity": 40,
        "ink": "Indigo",
        "status": "drying",
        "due_on": "2026-10-02",
        "notes": "Keep the oyster section.",
    }
    body.update(overrides)
    return http.post(
        "/api/jobs",
        json=body,
        headers={"X-Pressmark-Key": "test-key"},
    )


def test_api_requires_the_integration_key(client):
    response = client.get("/api/health")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Flask rejected the integration key."


def test_api_create_list_and_status(client):
    health = client.get("/api/health", headers={"X-Pressmark-Key": "test-key"})
    assert health.status_code == 200
    assert health.get_json()["service"] == "flask"

    created = create_via_api(client)
    assert created.status_code == 201
    job_id = created.get_json()["job"]["id"]

    listed = client.get("/api/jobs?q=Harbor", headers={"X-Pressmark-Key": "test-key"})
    payload = listed.get_json()
    assert payload["service"] == "flask"
    assert payload["jobs"][0]["title"] == "Bar menu"
    assert payload["total"] == 1

    moved = client.post(
        f"/api/jobs/{job_id}/status",
        json={"status": "on_press"},
        headers={"X-Pressmark-Key": "test-key"},
    )
    assert moved.status_code == 200
    assert moved.get_json()["job"]["status"] == "on_press"

    page = client.get("/")
    assert b"Bar menu" in page.data


def test_api_validation(client):
    response = create_via_api(client, client="", quantity="nope")
    assert response.status_code == 400
    errors = response.get_json()["errors"]
    assert "client" in errors
    assert "quantity" in errors
