from __future__ import annotations

import datetime
import json
import logging
from typing import Any
from urllib.parse import quote, unquote

import pytz
from django.conf import settings
from django.core import signing
from django.http import HttpRequest, HttpResponse
from django.template import Context, loader
from django.urls.base import reverse
from django.utils.functional import SimpleLazyObject

from .conf import PROTOCOL_VERSION, config

signer = SimpleLazyObject(lambda: signing.TimestampSigner())

logger = logging.getLogger(__name__)

ONE_YEAR = 365 * 24 * 60 * 60
DAY = 24 * 60 * 60


def is_local(request: HttpRequest) -> bool:  # noqa: ARG001
    return bool(config.REMOTE_SERVER)


def is_remote(request: HttpRequest) -> bool:
    return not is_local(request)


class SyncErrorResponse(HttpResponse):
    def __init__(self, content: bytes = b"", headers: dict[str, str] | None = None, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("content_type", "plain/text")
        kwargs.setdefault("status", 400)
        if not headers:
            headers = {config.RESPONSE_HEADER: PROTOCOL_VERSION}
        kwargs["headers"] = headers

        super().__init__(content, *args, **kwargs)


class SyncResponse(HttpResponse):
    def __init__(self, content: Any, headers: dict[str, str] | None = None, *args: Any, **kwargs: Any) -> None:
        data = wraps(json.dumps(content))
        kwargs.setdefault("content_type", "application/json")
        if not headers:
            headers = {config.RESPONSE_HEADER: PROTOCOL_VERSION}
        kwargs["headers"] = headers
        super().__init__(data, *args, **kwargs)

    def json(self) -> dict[str, Any]:
        return json.loads(unwrap(self.content))


def wraps(data: str) -> str:
    return json.dumps({"data": quote(data)})


def unwrap(payload: str) -> str:
    data = json.loads(payload)
    return unquote(data["data"])


def is_logged_to_remote(request: HttpRequest) -> str:
    return request.COOKIES.get(config.CREDENTIALS_COOKIE, None)


def sign_prod_credentials(username: str, password: str) -> str:
    return signer.sign_object({"username": username, "password": password})


def set_cookie(response: HttpResponse, key: str, value: str, days_expire: int = 7) -> None:
    max_age = ONE_YEAR if days_expire is None else days_expire * DAY
    expires = datetime.datetime.strftime(
        datetime.datetime.now(tz=pytz.UTC) + datetime.timedelta(seconds=max_age),
        "%a, %d-%b-%Y %H:%M:%S GMT",
    )
    response.set_cookie(
        key,
        value,
        max_age=max_age,
        expires=expires,
        domain=settings.SESSION_COOKIE_DOMAIN,
        secure=settings.SESSION_COOKIE_SECURE or None,
    )


def remote_reverse(urlname: str, args: Any | None = None, kwargs: Any | None = None) -> str:
    local = reverse(urlname, args=args, kwargs=kwargs)
    return config.REMOTE_SERVER + local.replace(config.LOCAL_ADMIN_URL, config.REMOTE_ADMIN_URL)


def invalidate_cache() -> None:
    pass


def get_client_ip(request: HttpRequest) -> str | None:
    """Returns remote client ip address from request.META.

    type: (WSGIRequest) -> Optional[Any]
    Naively yank the first IP address in an X-Forwarded-For header
    and assume this is correct.

    Note: Don't use this in security sensitive situations since this
    value may be forged from a client.
    """
    for x in [
        "HTTP_X_ORIGINAL_FORWARDED_FOR",
        "HTTP_X_FORWARDED_FOR",
        "HTTP_X_REAL_IP",
        "REMOTE_ADDR",
    ]:
        ip = request.META.get(x)
        if ip:
            return ip.split(",")[0].strip()
    return None


def render(
    request: HttpRequest,
    template_name: str,
    context: Context | None = None,
    content_type: str | None = None,
    status: int = 200,
    using: str | None = None,
    cookies: dict[str, str] | None = None,
) -> HttpResponse:
    content = loader.render_to_string(template_name, context, request, using=using)
    response = HttpResponse(content, content_type, status)
    if cookies:
        for k, v in cookies.items():
            response.set_cookie(k, v)

    return response


def get_remote_credentials(request: HttpRequest) -> dict[str, str]:
    try:
        return signer.unsign_object(request.COOKIES[config.CREDENTIALS_COOKIE])
    except (signing.BadSignature, KeyError):
        return {"username": "", "password": ""}
