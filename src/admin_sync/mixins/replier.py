from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from json import JSONDecodeError
from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.base import SerializationError

from admin_sync.utils import decode_natural_key
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


class ReplierMixin(BaseSyncMixin):
    def _reply(self, request: HttpRequest, natural_key: str) -> "AdminSyncResult":
        """Collect data to use as answer to a pull() request."""
        try:
            key = decode_natural_key(natural_key)
            obj = self.model._default_manager.get_by_natural_key(*key)  # type: ignore[attr-defined]
            data = self.protocol_class(request).serialize([obj])
            return AdminSyncResult(message="success", size=len(data), records=len(data), details=data, code=200)
        except ObjectDoesNotExist:
            return AdminSyncResult(message="error", size=0, records=0, details="Object not found", code=404)
        except JSONDecodeError as e:
            logger.exception(e)
            return AdminSyncResult(message="error", size=0, records=0, details="", code=400)
        except SerializationError as e:
            logger.exception(e)
            return AdminSyncResult(message="error", size=0, records=0, details="Unable to serialize data", code=500)
