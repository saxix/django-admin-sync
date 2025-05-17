from __future__ import annotations

from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from requests.auth import HTTPBasicAuth

    from admin_sync.types import SyncResponse


def send(url: str, payload: bytes, auth: HTTPBasicAuth | None = None) -> "SyncResponse":
    requests.post(url, data=payload, auth=auth, timeout=60)
    return {"message": "Success"}
