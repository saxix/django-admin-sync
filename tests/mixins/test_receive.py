from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse

from admin_sync.utils import wraps

if TYPE_CHECKING:
    from django_webtest import DjangoTestApp


def test_receive(app: DjangoTestApp, db):
    url = reverse("admin:auth_user_receive")
    res = app.post(url, wraps("{}"))
    assert res.status_code == 200
    assert res.json == {"message": "success", "records": 0, "size": 10, "details": "", "code": 200}


def test_receive_broken_payload(app: DjangoTestApp, db):
    url = reverse("admin:auth_user_receive")
    res = app.post(url, wraps("{sss}"), expect_errors=True)
    assert res.status_code == 500
    assert res.json == {"message": "error", "records": 0, "size": 13, "details": "", "code": 500}
