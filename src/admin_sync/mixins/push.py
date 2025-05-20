from __future__ import annotations

import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING

import requests
from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.serializers.base import DeserializationError
from django.shortcuts import render

from admin_sync.conf import config
from admin_sync.datastructures import AdminSyncReceiveResult
from admin_sync.mixins.base import BaseSyncMixin
from admin_sync.signals import admin_sync_data_received
from admin_sync.utils import remote_reverse, unwrap, wraps

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest, HttpResponse
    from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class PublishMixin(BaseSyncMixin):
    def can_publish(self, request: HttpRequest, pk: str | None = None, obj: Model | None = None) -> bool:  # noqa: ARG002 PLR6301
        return True

    def _receive(self, request: HttpRequest) -> "AdminSyncReceiveResult":
        try:
            raw_data = unwrap(request.body)
            data = self.protocol_class(request).deserialize(raw_data)
            admin_sync_data_received.send(sender=self, data=data)
            return AdminSyncReceiveResult(
                message="success", size=len(request.body), records=len(data), details="", status=200
            )
        except DeserializationError as e:
            logger.exception(e)
            return AdminSyncReceiveResult(message="error", size=len(request.body), records=0, details="", status=500)

    def _sync_send_handler(
        self, request: HttpRequest, obj: Model, auth: HTTPBasicAuth | None = None
    ) -> AdminSyncReceiveResult:
        try:
            url = remote_reverse(admin_urlname(self.model._meta, "receive"))  # type: ignore[arg-type]
            data = self.protocol_class(request).serialize([obj])
            response = requests.post(url, data=wraps(data), auth=auth, timeout=60)
            return AdminSyncReceiveResult(**response.json())
        except JSONDecodeError:
            return AdminSyncReceiveResult(status=500, details="Invalid JSON")

    def sync_publish(self, request: HttpRequest, pk: str) -> HttpResponse | None:
        """Send data to a Remote server"""
        context = self.get_common_context(request, pk, title="Publish to REMOTE", server=config.REMOTE_SERVER)
        obj = context["original"]
        if request.method == "POST":
            result = self._sync_send_handler(request, obj, auth=None)
            context["data"] = result.as_dict
            if result.status != 200:
                self.message_user(request, "Error", messages.ERROR)
            else:
                self.message_user(request, f"Published {result.records}", messages.SUCCESS)
        return render(request, "admin/admin_sync/publish.html", context)
