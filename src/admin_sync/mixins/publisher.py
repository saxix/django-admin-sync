from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from json import JSONDecodeError
from typing import TYPE_CHECKING

import requests
from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.shortcuts import render

from admin_sync.conf import config
from admin_sync.mixins.base import BaseSyncMixin
from admin_sync.utils import remote_reverse, wraps

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest, HttpResponse
    from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


@dataclass
class ReceiveResponse:
    status_code: int
    payload: dict[str, int | str]

    as_dict = asdict


class PublishMixin(BaseSyncMixin):
    def can_publish(self, request: HttpRequest, pk: str | None = None, obj: Model | None = None) -> bool:  # noqa: ARG002 PLR6301
        return True

    def _sync_send_handler(self, request, obj: Model, auth: HTTPBasicAuth | None = None) -> ReceiveResponse:
        try:
            url = remote_reverse(admin_urlname(self.model._meta, "receive"))  # type: ignore[arg-type]
            data = self.protocol_class(request).serialize([obj])
            response = requests.post(url, data=wraps(data), auth=auth, timeout=60)
            return ReceiveResponse(status_code=response.status_code, payload=response.json())
        except JSONDecodeError:
            return ReceiveResponse(status_code=500, payload={"error": "Invalid JSON"})

    def sync_publish(self, request: HttpRequest, pk: str) -> HttpResponse | None:
        """Send data to a Remote server"""
        context = self.get_common_context(request, pk, title="Publish to REMOTE", server=config.REMOTE_SERVER)
        obj = context["original"]
        if request.method == "POST":
            response = self._sync_send_handler(request, obj, auth=None)
            context["data"] = result = response.payload
            if response.status_code != 200:
                self.message_user(request, "Error", messages.ERROR)
            else:
                self.message_user(request, f"Published {result['records']}", messages.SUCCESS)
        return render(request, "admin/admin_sync/publish.html", context)
