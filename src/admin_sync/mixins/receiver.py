from __future__ import annotations

from typing import TYPE_CHECKING, Any

from admin_sync.utils import unwrap

from ..signals import admin_sync_data_received
from .base import BaseSyncMixin

if TYPE_CHECKING:
    from django.http import HttpRequest


class ReceiveMixin(BaseSyncMixin):
    def _receive(self, request: HttpRequest) -> list[list[Any]]:
        raw_data = unwrap(request.body)
        data = self.protocol_class(request).deserialize(raw_data)
        admin_sync_data_received.send(sender=self, data=data)
        return data
