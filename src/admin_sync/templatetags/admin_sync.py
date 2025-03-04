import json
import logging
from typing import Any

from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.db.models import Model
from django.template import Library
from django.urls import reverse
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)
register = Library()


@register.filter
def classname(v: Any) -> str:
    return v.__class__.__name__


@register.filter
def admin_url(obj: Model, arg: str) -> str:
    return reverse(admin_urlname(obj._meta, arg), args=[obj.pk])


@register.filter("escapedict")
def escapedict(data: dict[str, Any]) -> Any:
    if not isinstance(data, dict):
        return data
    for key, value in data.items():
        if isinstance(value, int) and not isinstance(value, bool):
            data[key] = int(mark_safe(value))
        else:
            data[key] = mark_safe(value)
    return json.dumps(data, indent=4)
