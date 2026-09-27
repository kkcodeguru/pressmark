from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .catalog import fetch_job, insert_job, list_jobs, remove_job, update_job_row, update_status
from .db import STATUS_LABELS, STATUSES
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
    job = fetch_job(job_id)
    if job is None:
        abort(404)
    return job


@bp.get("/")
def index():
    jobs, counts, total, status, query = list_jobs(
        request.args.get("status", ""),
        request.args.get("q", ""),
    )
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

    job_id = insert_job(data)
    flash("Job added to the board.", "success")
    return redirect(url_for("jobs.detail", job_id=job_id))


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

    update_job_row(job_id, data)
    flash("Job updated.", "success")
    return redirect(url_for("jobs.detail", job_id=job_id))


@bp.post("/jobs/<int:job_id>/status")
def set_status(job_id):
    validate_csrf()
    get_job_or_404(job_id)
    status = request.form.get("status", "")
    if status not in STATUSES:
        abort(400)
    update_status(job_id, status)
    flash(f"Moved to {STATUS_LABELS[status]}.", "success")
    return redirect(url_for("jobs.detail", job_id=job_id))


@bp.post("/jobs/<int:job_id>/delete")
def delete_job(job_id):
    validate_csrf()
    get_job_or_404(job_id)
    remove_job(job_id)
    flash("Job removed from the board.", "success")
    return redirect(url_for("jobs.index"))
