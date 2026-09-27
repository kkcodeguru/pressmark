import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings


class FlaskUnavailable(Exception):
    """The Flask process could not be reached."""


def call(method, path, body=None, query=None):
    url = settings.FLASK_API_URL.rstrip("/") + path
    if query:
        cleaned = {key: value for key, value in query.items() if value}
        if cleaned:
            url = f"{url}?{urllib.parse.urlencode(cleaned)}"

    headers = {
        "Accept": "application/json",
        "X-Pressmark-Key": settings.FLASK_API_KEY,
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"error": "Flask returned an unreadable response."}
        return exc.code, payload
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise FlaskUnavailable from exc
