import secrets

from flask import Blueprint, current_app, jsonify, request

from .catalog import (
    as_dict,
    fetch_job,
    insert_job,
    list_jobs,
    remove_job,
    update_job_row,
    update_status,
)
from .db import STATUSES
from .forms import parse_job

api = Blueprint("api", __name__, url_prefix="/api")


@api.before_request
def require_integration_key():
    expected = current_app.config["API_KEY"]
    sent = request.headers.get("X-Pressmark-Key", "")
    if not sent or not secrets.compare_digest(sent, expected):
        return jsonify({"error": "Flask rejected the integration key."}), 401
    return None


@api.get("/health")
def health():
    return jsonify({"service": "flask", "ok": True})


@api.get("/jobs")
def index():
    jobs, counts, total, status, query = list_jobs(
        request.args.get("status", ""),
        request.args.get("q", ""),
    )
    return jsonify(
        {
            "service": "flask",
            "jobs": [as_dict(job) for job in jobs],
            "counts": counts,
            "total": total,
            "status": status,
            "q": query,
        }
    )


@api.post("/jobs")
def create_job():
    data, errors = parse_job(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"errors": errors, "job": data}), 400
    job_id = insert_job(data)
    return jsonify({"job": as_dict(fetch_job(job_id))}), 201


@api.get("/jobs/<int:job_id>")
def detail(job_id):
    job = fetch_job(job_id)
    if job is None:
        return jsonify({"error": "That docket is not on the board."}), 404
    return jsonify({"job": as_dict(job)})


@api.put("/jobs/<int:job_id>")
def update_job(job_id):
    if fetch_job(job_id) is None:
        return jsonify({"error": "That docket is not on the board."}), 404
    data, errors = parse_job(request.get_json(silent=True) or {})
    if errors:
        data["id"] = job_id
        return jsonify({"errors": errors, "job": data}), 400
    update_job_row(job_id, data)
    return jsonify({"job": as_dict(fetch_job(job_id))})


@api.post("/jobs/<int:job_id>/status")
def set_status(job_id):
    if fetch_job(job_id) is None:
        return jsonify({"error": "That docket is not on the board."}), 404
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status", "")).strip()
    if status not in STATUSES:
        return jsonify({"errors": {"status": "Choose a status."}}), 400
    update_status(job_id, status)
    return jsonify({"job": as_dict(fetch_job(job_id))})


@api.delete("/jobs/<int:job_id>")
def delete_job(job_id):
    if fetch_job(job_id) is None:
        return jsonify({"error": "That docket is not on the board."}), 404
    remove_job(job_id)
    return jsonify({"ok": True})
