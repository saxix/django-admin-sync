from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

if TYPE_CHECKING:
    from django_webtest import DjangoTestApp


def test_publish(app: DjangoTestApp, admin_user, monkeypatch, responses):
    responses.add(responses.POST, "http://remote/auth/user/receive/", b"{}")
    url = reverse("admin:auth_user_change", args=[admin_user.pk])
    res = app.get(url, user=admin_user)
    res = res.click(linkid="btn-publish")
    res = res.forms["sync-remote-publish"].submit()
    assert "Published" in str(list(res.context["messages"])[0])


def test_publish_no_button(app: DjangoTestApp, user, monkeypatch, responses):
    url = reverse("admin:auth_user_change", args=[user.pk])
    res = app.get(url, user=user)
    with pytest.raises(IndexError, match=r"No matching elements found \(from 0 possible\)"):
        res.click(linkid="btn-send")


def test_publish_403(app: DjangoTestApp, user, monkeypatch, responses):
    monkeypatch.setattr("demoapp.admin.SyncUserAdmin.can_publish", lambda *a: False)
    url = reverse("admin:auth_user_publish", args=[user.pk])
    res = app.post(url, user=user, expect_errors=True)
    assert res.status_code == 403


def test_publish_failure(app: DjangoTestApp, user, monkeypatch, responses):
    responses.add(responses.POST, "http://remote/auth/user/receive/", json={})
    url = reverse("admin:auth_user_publish", args=[user.pk])
    res = app.post(url, user=user, expect_errors=True)
    assert res.status_code == 200
    assert "Published" in str(list(res.context["messages"])[0])
    assert str(list(res.context["messages"])[0]) == "Published {'message': 'Success'}"
