from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest import mock

from django.core.serializers.base import SerializationError
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode

from admin_sync.datastructures import SerializationResult
from admin_sync.utils import encode_natural_key

if TYPE_CHECKING:
    from django_webtest import DjangoTestApp


def test_reply(app: DjangoTestApp, admin_user):
    key = encode_natural_key(admin_user)
    url = reverse("admin:auth_user_reply", args=[key])
    res = app.get(url)
    assert res.status_code == 200
    payload = SerializationResult(**res.json)  # be sure it is a SerializationResult compatible payload
    assert payload.message == "success"
    assert payload.status == 200


def test_reply_broken_payload(app: DjangoTestApp, admin_user):
    key = "???"
    url = reverse("admin:auth_user_reply", args=[key])
    res = app.get(url, expect_errors=True)
    assert res.status_code == 400
    payload = SerializationResult(**res.json)  # be sure it is a SerializationResult compatible payload
    assert payload.message == "error"


def test_reply_404(app: DjangoTestApp, admin_user):
    # let create a missing  user natural key
    key = urlsafe_base64_encode(json.dumps([123]).encode())
    url = reverse("admin:auth_user_reply", args=[key])
    res = app.get(url, expect_errors=True)
    assert res.status_code == 404
    payload = SerializationResult(**res.json)  # be sure it is a SerializationResult compatible payload
    assert payload.status == 404


def test_reply_serialization(app: DjangoTestApp, admin_user):
    key = encode_natural_key(admin_user)
    url = reverse("admin:auth_user_reply", args=[key])
    with mock.patch("admin_sync.protocol.LoadDumpProtocol.serialize", side_effect=SerializationError()):
        res = app.get(url, expect_errors=True)
        assert res.status_code == 500
        payload = SerializationResult(**res.json)  # be sure it is a SerializationResult compatible payload
        assert payload.message == "error"
        assert payload.details == "Unable to serialize data"


def test_reply_exception(app: DjangoTestApp, admin_user):
    key = encode_natural_key(admin_user)
    url = reverse("admin:auth_user_reply", args=[key])
    with mock.patch("admin_sync.protocol.LoadDumpProtocol.serialize", side_effect=Exception()):
        res = app.get(url, expect_errors=True)
        assert res.status_code == 500
        assert res.json == {"message": "Unhandled Error", "code": 500}
