from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from django.core.serializers.base import DeserializationError

from admin_sync.utils import unwrap

from ..signals import admin_sync_data_received
from .base import BaseSyncMixin

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


@dataclass
class AdminSyncResult:
    message: str
    details: str
    code: int
    size: int
    records: int

    as_dict = asdict


class ReceiveMixin(BaseSyncMixin):
    def _receive(self, request: HttpRequest) -> "AdminSyncResult":
        try:
            raw_data = unwrap(request.body)
            data = self.protocol_class(request).deserialize(raw_data)
            admin_sync_data_received.send(sender=self, data=data)
            return AdminSyncResult(message="success", size=len(request.body), records=len(data), details="", code=200)
        except DeserializationError as e:
            logger.exception(e)
            return AdminSyncResult(message="error", size=len(request.body), records=0, details="", code=500)
