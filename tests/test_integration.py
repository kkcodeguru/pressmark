import json
import threading
import urllib.request

import pytest
from django.test import Client, override_settings
from werkzeug.serving import make_server

from app import create_app


class _Server(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.server = make_server("127.0.0.1", 0, app)
        self.port = self.server.server_address[1]

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


@pytest.fixture
def flask_service(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "integration.sqlite"),
            "SECRET_KEY": "test-secret",
            "API_KEY": "test-key",
        }
    )
    server = _Server(app)
    server.start()
    yield server
    server.stop()


def test_django_board_reads_a_job_created_in_flask(flask_service):
    body = json.dumps(
        {
            "client": "North Room Books",
            "title": "Poetry broadside",
            "kind": "broadside",
            "quantity": 60,
            "ink": "Warm black",
            "status": "queued",
            "due_on": "2026-11-01",
            "notes": "Numbered in pencil.",
        }
    ).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{flask_service.port}/api/jobs",
        data=body,
        headers={"Content-Type": "application/json", "X-Pressmark-Key": "test-key"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        assert response.status == 201

    with override_settings(
        FLASK_API_URL=f"http://127.0.0.1:{flask_service.port}",
        FLASK_API_KEY="test-key",
    ):
        response = Client().get("/")

    assert response.status_code == 200
    assert b"Poetry broadside" in response.content
    assert b"Django renders this page" in response.content
