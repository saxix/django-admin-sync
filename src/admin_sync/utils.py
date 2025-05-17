from __future__ import annotations

import logging
import zlib
from typing import TYPE_CHECKING, Any

from django.core import signing
from django.urls.base import reverse
from django.utils.functional import SimpleLazyObject

from .conf import config

if TYPE_CHECKING:
    from django.http import HttpRequest

signer = SimpleLazyObject(lambda: signing.TimestampSigner())

logger = logging.getLogger(__name__)

ONE_YEAR = 365 * 24 * 60 * 60
DAY = 24 * 60 * 60


def wraps(data: str) -> bytes:
    return zlib.compress(data.encode())


def unwrap(payload: bytes) -> str:
    return zlib.decompress(payload).decode()


def remote_reverse(urlname: str, args: Any | None = None, kwargs: Any | None = None) -> str:
    local = reverse(urlname, args=args, kwargs=kwargs)
    return config.REMOTE_SERVER + local.replace(config.LOCAL_ADMIN_URL, config.REMOTE_ADMIN_URL)


def get_remote_credentials(request: HttpRequest) -> dict[str, str]:
    return {"username": config.REMOTE_USER, "password": config.REMOTE_PASSWORD}
