from datetime import date

from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    if mapping is None:
        return ""
    return mapping.get(key, "")


@register.filter
def pretty_date(value):
    if not value:
        return "No due date"
    parsed = date.fromisoformat(value)
    return f"{parsed.day} {parsed.strftime('%b %Y')}"
