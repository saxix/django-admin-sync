from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from admin_sync.datastructures import AdminSyncReceiveResult

if TYPE_CHECKING:
    from django_webtest import DjangoTestApp


def test_publish(app: DjangoTestApp, admin_user, monkeypatch, responses):
    responses.add(
        responses.POST,
        "http://remote/auth/user/receive/",
        json=AdminSyncReceiveResult(message="success", size=10, records=10, details="", status=200).as_dict(),
    )
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


def test_publish_none(app: DjangoTestApp, user, monkeypatch, responses):
    responses.add(
        responses.POST,
        "http://remote/auth/user/receive/",
        json=AdminSyncReceiveResult(message="error", size=0, records=0, details="", status=200).as_dict(),
    )
    url = reverse("admin:auth_user_publish", args=[user.pk])
    res = app.post(url, user=user)
    assert res.status_code == 200
    assert "Published" in str(list(res.context["messages"])[0])
    assert str(list(res.context["messages"])[0]) == "Published 0"


def test_publish_remote_exception(app: DjangoTestApp, user, monkeypatch, responses):
    responses.add(responses.POST, "http://remote/auth/user/receive/", "", status=500)
    url = reverse("admin:auth_user_publish", args=[user.pk])
    res = app.post(url, user=user, expect_errors=True)
    assert res.status_code == 200
    assert str(list(res.context["messages"])[0]) == "Error"
