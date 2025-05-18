import logging
from typing import Any

from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.db.models import Model
from django.template import Library
from django.urls import reverse

from ..utils import remote_reverse

logger = logging.getLogger(__name__)
register = Library()


@register.filter
def classname(v: Any) -> str:
    return v.__class__.__name__


@register.filter
def admin_url(obj: Model, arg: str) -> str:
    return reverse(admin_urlname(obj._meta, arg), args=[obj.pk])  # type: ignore[arg-type]


@register.filter
def remote_url(obj: Model, arg: str) -> str:
    return remote_reverse(admin_urlname(obj._meta, arg), args=[obj.pk])  # type: ignore[arg-type]
