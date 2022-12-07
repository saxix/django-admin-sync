import datetime
import io
import json
import logging
import tempfile
from itertools import chain
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, unquote

from django.conf import settings
from django.core import signing
from django.core.management import call_command
from django.core.serializers import get_serializer
from django.db.models import ForeignKey, ManyToManyField, OneToOneField, OneToOneRel
from django.http import HttpResponse
from django.template import loader
from django.urls.base import reverse

from .compat import (
    disable_concurrency,
    reversion_create_revision,
    reversion_set_comment,
    reversion_set_user,
)
from .conf import PROTOCOL_VERSION, config

signer = signing.TimestampSigner()

logger = logging.getLogger(__name__)


def is_local(request):
    return bool(config.REMOTE_SERVER)


def is_remote(request):
    return not is_local(request)


# def collect_data(reg: Iterable, collect_related) -> str:
#     c = ForeignKeysCollector(collect_related)
#     c.collect(reg)
#     json = get_serializer("json")()
#     return json.serialize(
#         c.data, use_natural_foreign_keys=True, use_natural_primary_keys=True, indent=3
#     )


class SyncResponse(HttpResponse):
    def __init__(self, content=b"", headers=None, *args, **kwargs):
        data = wraps(json.dumps(content))
        kwargs.setdefault("content_type", "application/json")
        if not headers:
            headers = {config.RESPONSE_HEADER: PROTOCOL_VERSION}
        super().__init__(data, headers=headers, *args, **kwargs)

    def json(self):
        return json.loads(unwrap(self.content))


# def loaddata_from_stream(request, payload):
#     workdir = Path(".").absolute()
#     remote_ip = get_client_ip(request)
#     kwargs = {
#         "dir": workdir,
#         "prefix": "~LOADDATA",
#         "suffix": ".json",
#         "delete": False,
#     }
#     with tempfile.NamedTemporaryFile(**kwargs) as fdst:
#         assert isinstance(fdst.write, object)
#         fdst.write(payload.encode())
#         fixture = (workdir / fdst.name).absolute()
#     with disable_concurrency():
#         with reversion_create_revision():
#             reversion_set_user(request.user)
#             reversion_set_comment(f"loaddata from {remote_ip}")
#             out = io.StringIO()
#             call_command("loaddata", fixture, stdout=out, verbosity=3)
#     Path(fixture).unlink()
#     return out.getvalue()


def wraps(data: str) -> str:
    return json.dumps({"data": quote(data)})


def unwrap(payload: str) -> str:
    data = json.loads(payload)
    return unquote(data["data"])


def is_logged_to_remote(request):
    return request.COOKIES.get(config.CREDENTIALS_COOKIE, None)


def sign_prod_credentials(username, password):
    return signer.sign_object({"username": username, "password": password})


def set_cookie(response, key, value, days_expire=7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(
        datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
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


def remote_reverse(urlname, args=None, kwargs=None):
    local = reverse(urlname, args=args, kwargs=kwargs)
    return config.REMOTE_SERVER + local.replace(
        config.LOCAL_ADMIN_URL, config.REMOTE_ADMIN_URL
    )


def invalidate_cache():
    pass


def get_client_ip(request):
    """
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


def render(
    request,
    template_name,
    context=None,
    content_type=None,
    status=None,
    using=None,
    cookies=None,
):
    """
    Return a HttpResponse whose content is filled with the result of calling
    django.template.loader.render_to_string() with the passed arguments.
    """
    content = loader.render_to_string(template_name, context, request, using=using)
    response = HttpResponse(content, content_type, status)
    if cookies:
        for k, v in cookies.items():
            response.set_cookie(k, v)

    return response


def get_remote_credentials(request):
    try:
        credentials = signer.unsign_object(request.COOKIES[config.CREDENTIALS_COOKIE])
        return credentials
    except (signing.BadSignature, KeyError):
        return {"username": "", "password": ""}
