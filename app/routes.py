from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .db import STATUS_LABELS, STATUSES, get_db
from .forms import parse_job
from .security import validate_csrf

bp = Blueprint("jobs", __name__)


def blank_job():
    return {
        "client": "",
        "title": "",
        "kind": "card",
        "quantity": "",
        "ink": "",
        "status": "queued",
        "due_on": "",
        "notes": "",
    }


def as_form(job):
    data = {key: job[key] for key in job.keys()}
    if data["due_on"] is None:
        data["due_on"] = ""
    return data


def get_job_or_404(job_id):
    job = get_db().execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job is None:
        abort(404)
    return job


def like_pattern(term):
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def job_counts():
    rows = get_db().execute(
        "SELECT status, COUNT(*) AS n FROM jobs GROUP BY status"
    ).fetchall()
    counts = {key: 0 for key in STATUSES}
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] = row["n"]
    return counts, sum(counts.values())


@bp.get("/")
def index():
    status = request.args.get("status", "").strip()
    if status not in STATUSES:
        status = ""
    query = request.args.get("q", "").strip()

    sql = "SELECT * FROM jobs WHERE 1 = 1"
    params = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if query:
        sql += " AND (client LIKE ? ESCAPE '\\' OR title LIKE ? ESCAPE '\\' OR ink LIKE ? ESCAPE '\\')"
        pattern = like_pattern(query)
        params.extend([pattern, pattern, pattern])
    sql += """
        ORDER BY CASE status
            WHEN 'on_press' THEN 0
            WHEN 'drying' THEN 1
            WHEN 'queued' THEN 2
            ELSE 3
        END,
        due_on IS NULL,
        due_on ASC,
        id DESC
    """
    jobs = get_db().execute(sql, params).fetchall()
    counts, total = job_counts()
    return render_template(
        "index.html",
        jobs=jobs,
        counts=counts,
        total=total,
        status=status,
        q=query,
    )


@bp.get("/jobs/new")
def new_job():
    return render_template("form.html", mode="new", job=blank_job(), errors={})


@bp.post("/jobs")
def create_job():
    validate_csrf()
    data, errors = parse_job(request.form)
    if errors:
        return render_template("form.html", mode="new", job=data, errors=errors), 400

    cursor = get_db().execute(
        """
        INSERT INTO jobs (client, title, kind, quantity, ink, status, due_on, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["client"],
            data["title"],
            data["kind"],
            data["quantity"],
            data["ink"],
            data["status"],
            data["due_on"],
            data["notes"],
        ),
    )
    get_db().commit()
    flash("Job added to the board.", "success")
    return redirect(url_for("jobs.detail", job_id=cursor.lastrowid))


@bp.get("/jobs/<int:job_id>")
def detail(job_id):
    job = get_job_or_404(job_id)
    return render_template("detail.html", job=job)


@bp.get("/jobs/<int:job_id>/edit")
def edit_job(job_id):
    job = get_job_or_404(job_id)
    return render_template("form.html", mode="edit", job=as_form(job), errors={})


@bp.post("/jobs/<int:job_id>")
def update_job(job_id):
    validate_csrf()
    get_job_or_404(job_id)
    data, errors = parse_job(request.form)
    if errors:
        data["id"] = job_id
        return render_template("form.html", mode="edit", job=data, errors=errors), 400

    get_db().execute(
        """
        UPDATE jobs
        SET client = ?, title = ?, kind = ?, quantity = ?, ink = ?, status = ?, due_on = ?, notes = ?
        WHERE id = ?
        """,
        (
            data["client"],
            data["title"],
            data["kind"],
            data["quantity"],
            data["ink"],
            data["status"],
            data["due_on"],
            data["notes"],
            job_id,
        ),
    )
    get_db().commit()
    flash("Job updated.", "success")
    return redirect(url_for("jobs.detail", job_id=job_id))


@bp.post("/jobs/<int:job_id>/status")
def set_status(job_id):
    validate_csrf()
    get_job_or_404(job_id)
    status = request.form.get("status", "")
    if status not in STATUSES:
        abort(400)
    get_db().execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
    get_db().commit()
    flash(f"Moved to {STATUS_LABELS[status]}.", "success")
    return redirect(url_for("jobs.detail", job_id=job_id))


@bp.post("/jobs/<int:job_id>/delete")
def delete_job(job_id):
    validate_csrf()
    get_job_or_404(job_id)
    get_db().execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    get_db().commit()
    flash("Job removed from the board.", "success")
    return redirect(url_for("jobs.index"))
