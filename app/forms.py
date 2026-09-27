from datetime import date

from .db import KINDS, STATUSES


def parse_job(form):
    raw = {
        "client": form.get("client", "").strip(),
        "title": form.get("title", "").strip(),
        "kind": form.get("kind", "").strip(),
        "quantity": form.get("quantity", "").strip(),
        "ink": form.get("ink", "").strip(),
        "status": form.get("status", "").strip(),
        "due_on": form.get("due_on", "").strip(),
        "notes": form.get("notes", "").strip(),
    }
    errors = {}

    if not raw["client"]:
        errors["client"] = "Client name is required."
    elif len(raw["client"]) > 80:
        errors["client"] = "Keep the client name under 80 characters."

    if not raw["title"]:
        errors["title"] = "Piece title is required."
    elif len(raw["title"]) > 120:
        errors["title"] = "Keep the piece title under 120 characters."

    if raw["kind"] not in KINDS:
        errors["kind"] = "Choose a piece type."

    quantity = None
    if raw["quantity"] == "":
        errors["quantity"] = "Quantity is required."
    else:
        try:
            quantity = int(raw["quantity"])
        except ValueError:
            errors["quantity"] = "Quantity must be a whole number."
        else:
            if quantity < 1 or quantity > 100_000:
                errors["quantity"] = "Quantity must be between 1 and 100,000."

    if not raw["ink"]:
        errors["ink"] = "Ink color is required."
    elif len(raw["ink"]) > 40:
        errors["ink"] = "Keep the ink name under 40 characters."

    if raw["status"] not in STATUSES:
        errors["status"] = "Choose a status."

    if raw["due_on"]:
        try:
            date.fromisoformat(raw["due_on"])
        except ValueError:
            errors["due_on"] = "Use a valid date."
    if len(raw["notes"]) > 2000:
        errors["notes"] = "Keep notes under 2,000 characters."

    if errors:
        return raw, errors

    cleaned = dict(raw)
    cleaned["quantity"] = quantity
    cleaned["due_on"] = raw["due_on"] or None
    return cleaned, {}
