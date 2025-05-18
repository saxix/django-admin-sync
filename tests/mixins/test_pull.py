from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

if TYPE_CHECKING:
    from django_webtest import DjangoTestApp


def test_pull(app: DjangoTestApp, admin_user, monkeypatch, responses):
    responses.add(
        responses.POST,
        re.compile(r"http://remote/auth/user/.*/reply/"),
        json={"status": "success", "records": 10, "size": 13},
    )
    url = reverse("admin:auth_user_change", args=[admin_user.pk])
    res = app.get(url, user=admin_user)
    res = res.click(linkid="btn-pull")
    res = res.forms["sync-remote-pull"].submit()
    assert str(list(res.context["messages"])[0]) == "Pulled 10 records"


def test_pull_no_button(app: DjangoTestApp, user, monkeypatch, responses):
    url = reverse("admin:auth_user_change", args=[user.pk])
    res = app.get(url, user=user)
    with pytest.raises(IndexError, match=r"No matching elements found \(from 0 possible\)"):
        res.click(linkid="btn-send")


def test_pull_403(app: DjangoTestApp, user, monkeypatch, responses):
    monkeypatch.setattr("demoapp.admin.SyncUserAdmin.can_pull", lambda *a: False)
    url = reverse("admin:auth_user_pull", args=[user.pk])
    res = app.post(url, user=user, expect_errors=True)
    assert res.status_code == 403


def test_pull_failure(app: DjangoTestApp, user, monkeypatch, responses):
    responses.add(
        responses.POST,
        re.compile(r"http://remote/auth/user/.*/reply/"),
        json={"status": "error", "records": 0, "size": 13},
    )
    url = reverse("admin:auth_user_pull", args=[user.pk])
    res = app.post(url, user=user, expect_errors=True)
    assert res.status_code == 200
    assert str(list(res.context["messages"])[0]) == "Pulled 0 records"


def test_pull_remote_exception(app: DjangoTestApp, user, monkeypatch, responses):
    responses.add(responses.POST, re.compile(r"http://remote/auth/user/.*/reply/"), status=500)
    url = reverse("admin:auth_user_pull", args=[user.pk])
    res = app.post(url, user=user, expect_errors=True)
    assert res.status_code == 200
    assert str(list(res.context["messages"])[0]) == "Error"
