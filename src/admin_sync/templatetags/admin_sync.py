import logging

from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.template import Library, Node
from django.urls import reverse

logger = logging.getLogger(__name__)
register = Library()


@register.filter
def classname(v):
    return v.__class__.__name__


@register.filter
def admin_url(obj, arg):
    return reverse(admin_urlname(obj._meta, arg), args=[obj.pk])
