from unittest.mock import patch

from django.test import TestCase, override_settings

from shop.flask_api import FlaskUnavailable


JOB = {
    "id": 7,
    "client": "Adler & Pine",
    "title": "Winter wedding suite",
    "kind": "invitation",
    "quantity": 150,
    "ink": "Bone black",
    "status": "queued",
    "due_on": "2026-10-12",
    "notes": "Belly band.",
}

LISTING = {
    "service": "flask",
    "jobs": [JOB],
    "counts": {"queued": 1, "on_press": 0, "drying": 0, "delivered": 0},
    "total": 1,
    "status": "",
    "q": "",
}


@override_settings(FLASK_API_URL="http://flask.test", FLASK_API_KEY="test-key")
class ShopBoardTests(TestCase):
    @patch("shop.views.call")
    def test_board_renders_jobs_from_flask(self, call):
        call.return_value = (200, LISTING)
        response = self.client.get("/")
        self.assertContains(response, "Winter wedding suite")
        self.assertContains(response, "Django renders this page")
        self.assertContains(response, "Flask service")
        call.assert_called_once()

    @patch("shop.views.call", side_effect=FlaskUnavailable())
    def test_board_explains_when_flask_is_down(self, _call):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Flask service is not running.", status_code=503)

    @patch("shop.views.call")
    def test_create_posts_the_form_to_flask(self, call):
        call.return_value = (201, {"job": JOB})
        response = self.client.post(
            "/jobs/create",
            {
                "client": "Adler & Pine",
                "title": "Winter wedding suite",
                "kind": "invitation",
                "quantity": "150",
                "ink": "Bone black",
                "status": "queued",
                "due_on": "2026-10-12",
                "notes": "Belly band.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/jobs/7")
        method, path = call.call_args.args[:2]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/api/jobs")
        self.assertEqual(call.call_args.kwargs["body"]["title"], "Winter wedding suite")
