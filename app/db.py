import sqlite3
from datetime import date, timedelta

from flask import current_app, g

STATUSES = ("queued", "on_press", "drying", "delivered")
KINDS = ("invitation", "card", "poster", "broadside", "menu")

STATUS_LABELS = {
    "queued": "Queued",
    "on_press": "On press",
    "drying": "Drying",
    "delivered": "Delivered",
}

KIND_LABELS = {
    "invitation": "Invitation",
    "card": "Card",
    "poster": "Poster",
    "broadside": "Broadside",
    "menu": "Menu",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client TEXT NOT NULL,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    ink TEXT NOT NULL,
    status TEXT NOT NULL,
    due_on TEXT,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    connection = get_db()
    existing = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'jobs'"
    ).fetchone()
    connection.executescript(SCHEMA)
    connection.commit()
    return existing is None


def _iso(today, days):
    return (today + timedelta(days=days)).isoformat()


def seed_jobs():
    connection = get_db()
    count = connection.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()["n"]
    if count:
        return
    today = date.today()
    rows = [
        (
            "Adler & Pine",
            "Winter wedding suite",
            "invitation",
            150,
            "Bone black",
            "on_press",
            _iso(today, 6),
            "Two-color invitation with a copper belly band.",
        ),
        (
            "Harbor & Rye",
            "Bar menu",
            "menu",
            40,
            "Indigo",
            "drying",
            _iso(today, 1),
            "Replace the old rye list. Keep the oyster section.",
        ),
        (
            "City Archive",
            "Evening lecture poster",
            "poster",
            80,
            "Cadmium red",
            "queued",
            _iso(today, -2),
            "The lecture date changed. Reprint before the doors open.",
        ),
        (
            "June Calder",
            "Calling cards",
            "card",
            200,
            "Forest green",
            "delivered",
            _iso(today, -10),
            "Left with the studio on King Street.",
        ),
        (
            "North Room Books",
            "Poetry broadside",
            "broadside",
            60,
            "Warm black",
            "queued",
            _iso(today, 12),
            "Edition of 60, numbered in pencil on the press.",
        ),
        (
            "Marlow Hotel",
            "Room directory",
            "card",
            25,
            "Copper",
            "on_press",
            _iso(today, 3),
            "One card per floor. The proof is approved.",
        ),
    ]
    connection.executemany(
        """
        INSERT INTO jobs (client, title, kind, quantity, ink, status, due_on, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        created = init_db()
        if created and not app.config.get("TESTING"):
            seed_jobs()
