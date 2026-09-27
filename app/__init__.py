import os
from datetime import date

from flask import Flask, render_template

from .security import csrf_token

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def create_app(test_config=None):
    app = Flask(
        __name__,
        instance_path=os.path.join(ROOT, "instance"),
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "pressmark-dev-only"),
        DATABASE=os.path.join(app.instance_path, "pressmark.sqlite"),
    )
    if test_config:
        app.config.update(test_config)

    database_dir = os.path.dirname(app.config["DATABASE"])
    if database_dir:
        os.makedirs(database_dir, exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    from . import db

    db.init_app(app)

    from .db import KIND_LABELS, KINDS, STATUS_LABELS, STATUSES
    from .routes import bp

    app.register_blueprint(bp)

    @app.template_filter("pretty_date")
    def pretty_date(value):
        if not value:
            return "No due date"
        parsed = date.fromisoformat(value)
        return f"{parsed.day} {parsed.strftime('%b %Y')}"

    @app.context_processor
    def inject_globals():
        return {
            "csrf_token": csrf_token(),
            "status_labels": STATUS_LABELS,
            "kind_labels": KIND_LABELS,
            "statuses": STATUSES,
            "kinds": KINDS,
            "today": date.today().isoformat(),
        }

    @app.errorhandler(400)
    def bad_request(_error):
        return (
            render_template(
                "error.html",
                code=400,
                heading="That form could not be saved.",
                message="Refresh the page and submit it again.",
            ),
            400,
        )

    @app.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "error.html",
                code=404,
                heading="That docket is not on the board.",
                message="The page or job number does not exist.",
            ),
            404,
        )

    @app.errorhandler(500)
    def server_error(_error):
        return (
            render_template(
                "error.html",
                code=500,
                heading="The press stopped.",
                message="Something went wrong while loading this page. Try the board again.",
            ),
            500,
        )

    return app
