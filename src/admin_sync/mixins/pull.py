from __future__ import annotations

import logging
from json import JSONDecodeError
from typing import TYPE_CHECKING

import requests
from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.base import DeserializationError, SerializationError
from django.shortcuts import render

from admin_sync.conf import config
from admin_sync.utils import decode_natural_key, encode_natural_key, remote_reverse

from ..datastructures import SerializationResult
from .base import BaseSyncMixin

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest, HttpResponse
    from requests.auth import HTTPBasicAuth

    from admin_sync.types import NaturalKeyModel

logger = logging.getLogger(__name__)


class PullMixin(BaseSyncMixin):
    def can_pull(self, request: HttpRequest, pk: str | None = None, obj: Model | None = None) -> bool:  # noqa: ARG002 PLR6301
        return True

    def _reply(self, request: HttpRequest, natural_key: str) -> "SerializationResult":
        """Collect data to use as answer to a pull() request."""
        try:
            key = decode_natural_key(natural_key)
            obj = self.model._default_manager.get_by_natural_key(*key)  # type: ignore[attr-defined]
            pr = self.protocol_class(request)
            data = pr.serialize([obj])
            return SerializationResult(message="success", size=len(data), payload=data, records=pr.collected_records)
        except ObjectDoesNotExist:
            return SerializationResult(message="error", size=0, details="Object not found", status=404)
        except JSONDecodeError as e:
            logger.exception(e)
            return SerializationResult(message="error", size=0, details="", status=400)
        except SerializationError as e:
            logger.exception(e)
            return SerializationResult(message="error", size=0, details="Unable to serialize data", status=500)

    def _sync_pull_handler(
        self, request: HttpRequest, obj: "NaturalKeyModel", auth: HTTPBasicAuth | None = None
    ) -> SerializationResult:
        try:
            key = encode_natural_key(obj)
            url = remote_reverse(admin_urlname(self.model._meta, "reply"), args=[key])  # type: ignore[arg-type]
            response = requests.post(url, auth=auth, timeout=60)
            return SerializationResult(**response.json())
        except (JSONDecodeError, DeserializationError):
            return SerializationResult(status=500, message="error", details="Invalid JSON")

    def sync_pull_data(self, request: HttpRequest, pk: str) -> HttpResponse | None:
        context = self.get_common_context(request, pk, title="Pull from REMOTE", server=config.REMOTE_SERVER)
        obj = context["original"]
        if request.method == "POST":
            response = self._sync_pull_handler(request, obj, auth=None)
            context["data"] = response
            if response.status != 200:
                self.message_user(request, "Error", messages.ERROR)
            else:
                try:
                    records = response.payload
                    processed = self.protocol_class(request).deserialize(records)
                    self.message_user(request, f"Pulled {len(processed)} records", messages.SUCCESS)
                except DeserializationError as e:
                    logger.exception(e)
                    self.message_user(request, "Error processing received data (DeserializationError)", messages.ERROR)

        return render(request, "admin/admin_sync/pull.html", context)
