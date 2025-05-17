from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.shortcuts import render

from admin_sync.api import send
from admin_sync.conf import config
from admin_sync.mixins.base import BaseSyncMixin
from admin_sync.utils import remote_reverse, wraps

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class PublishMixin(BaseSyncMixin):
    def can_publish(self, request: HttpRequest, pk: str | None = None, obj: Model | None = None) -> bool:  # noqa: ARG002 PLR6301
        return True

    def _publish(self, request: HttpRequest, pk: str) -> HttpResponse | None:
        context = self.get_common_context(request, pk, title="Publish to REMOTE", server=config.REMOTE_SERVER)
        obj = context["original"]
        if request.method == "POST":
            data = self.protocol_class(request).serialize([obj])
            url = remote_reverse(admin_urlname(self.model._meta, "receive"))
            result = send(url, wraps(data))
            context["data"] = result
            self.message_user(request, f"Published {result}", messages.SUCCESS)
        return render(request, "admin/admin_sync/publish.html", context)
