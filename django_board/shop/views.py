from datetime import date

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .constants import KIND_LABELS, KINDS, STATUS_LABELS, STATUSES
from .flask_api import FlaskUnavailable, call

FIELDS = ("client", "title", "kind", "quantity", "ink", "status", "due_on", "notes")


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


def board(request, **extra):
    context = {
        "statuses": STATUSES,
        "status_labels": STATUS_LABELS,
        "kind_labels": KIND_LABELS,
        "kinds": KINDS,
        "today": date.today().isoformat(),
    }
    context.update(extra)
    return context


def flask_down(request, payload=None, status=503):
    payload = payload or {}
    if status == 401 or payload.get("error", "").startswith("Flask rejected"):
        status = 502
        heading = "Flask rejected the integration key."
        message = "Set PRESSMARK_API_KEY to the same value for the Django board and the Flask service."
    else:
        heading = "Flask service is not running."
        message = "Start it with python run.py on port 5341, then reload this board."
    return render(
        request,
        "shop/unavailable.html",
        board(request, heading=heading, message=message, detail=payload.get("error", "")),
        status=status,
    )


def missing(request):
    return render(request, "shop/not_found.html", board(request), status=404)


@require_GET
def index(request):
    try:
        code, payload = call(
            "GET",
            "/api/jobs",
            query={"status": request.GET.get("status", ""), "q": request.GET.get("q", "")},
        )
    except FlaskUnavailable:
        return flask_down(request)
    if code != 200:
        return flask_down(request, payload, status=code)
    return render(
        request,
        "shop/index.html",
        board(
            request,
            jobs=payload["jobs"],
            counts=payload["counts"],
            total=payload["total"],
            status=payload["status"],
            q=payload["q"],
        ),
    )


@require_GET
def new_job(request):
    return render(request, "shop/form.html", board(request, mode="new", job=blank_job(), errors={}))


@require_POST
def create_job(request):
    body = {field: request.POST.get(field, "") for field in FIELDS}
    try:
        code, payload = call("POST", "/api/jobs", body=body)
    except FlaskUnavailable:
        return flask_down(request)
    if code == 400 and payload.get("errors"):
        return render(
            request,
            "shop/form.html",
            board(request, mode="new", job=payload.get("job", body), errors=payload["errors"]),
            status=400,
        )
    if code != 201:
        return flask_down(request, payload, status=code)
    messages.success(request, "Job added through Flask.")
    return redirect("shop:detail", job_id=payload["job"]["id"])


@require_GET
def detail(request, job_id):
    try:
        code, payload = call("GET", f"/api/jobs/{job_id}")
    except FlaskUnavailable:
        return flask_down(request)
    if code == 404:
        return missing(request)
    if code != 200:
        return flask_down(request, payload, status=code)
    return render(request, "shop/detail.html", board(request, job=payload["job"]))


@require_GET
def edit_job(request, job_id):
    try:
        code, payload = call("GET", f"/api/jobs/{job_id}")
    except FlaskUnavailable:
        return flask_down(request)
    if code == 404:
        return missing(request)
    if code != 200:
        return flask_down(request, payload, status=code)
    job = payload["job"]
    if not job.get("due_on"):
        job["due_on"] = ""
    return render(request, "shop/form.html", board(request, mode="edit", job=job, errors={}))


@require_POST
def update_job(request, job_id):
    body = {field: request.POST.get(field, "") for field in FIELDS}
    try:
        code, payload = call("PUT", f"/api/jobs/{job_id}", body=body)
    except FlaskUnavailable:
        return flask_down(request)
    if code == 404:
        return missing(request)
    if code == 400 and payload.get("errors"):
        job = payload.get("job", body)
        job["id"] = job_id
        return render(
            request,
            "shop/form.html",
            board(request, mode="edit", job=job, errors=payload["errors"]),
            status=400,
        )
    if code != 200:
        return flask_down(request, payload, status=code)
    messages.success(request, "Job updated through Flask.")
    return redirect("shop:detail", job_id=job_id)


@require_POST
def set_status(request, job_id):
    try:
        code, payload = call(
            "POST",
            f"/api/jobs/{job_id}/status",
            body={"status": request.POST.get("status", "")},
        )
    except FlaskUnavailable:
        return flask_down(request)
    if code == 404:
        return missing(request)
    if code != 200:
        return flask_down(request, payload, status=code)
    label = STATUS_LABELS.get(payload["job"]["status"], payload["job"]["status"])
    messages.success(request, f"Flask moved this job to {label}.")
    return redirect("shop:detail", job_id=job_id)


@require_POST
def delete_job(request, job_id):
    try:
        code, payload = call("DELETE", f"/api/jobs/{job_id}")
    except FlaskUnavailable:
        return flask_down(request)
    if code == 404:
        return missing(request)
    if code != 200:
        return flask_down(request, payload, status=code)
    messages.success(request, "Job removed through Flask.")
    return redirect("shop:index")
