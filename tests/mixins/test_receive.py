from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse

from admin_sync.utils import wraps

if TYPE_CHECKING:
    from django_webtest import DjangoTestApp


def test_receive(app: DjangoTestApp, admin_user, monkeypatch, responses):
    url = reverse("admin:auth_user_receive")
    res = app.post(url, wraps("{}"))
    assert res.status_code == 200
    assert res.json == {"status": "success", "records": 0, "size": 10}
