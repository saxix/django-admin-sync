from django.urls import reverse


def test_post_remote_data_403(app, admin_user, monkeypatch, responses):
    monkeypatch.setattr("admin_sync.mixin.is_logged_to_remote", lambda s: True)
    responses.add(responses.POST, "http://remote/auth/user/receive/", status=403)
    url = reverse("admin:auth_user_publish", args=[admin_user.pk])
    res = app.post(url, user=admin_user, expect_errors=True)
    assert res.status_code == 302


def test_post_remote_data_404(app, admin_user, monkeypatch, responses):
    monkeypatch.setattr("admin_sync.mixin.is_logged_to_remote", lambda s: True)
    responses.add(responses.POST, "http://remote/auth/user/receive/", status=404)
    url = reverse("admin:auth_user_publish", args=[admin_user.pk])
    res = app.post(url, user=admin_user, expect_errors=True)
    assert res.status_code == 200
    assert (
        str(list(res.context["messages"])[0])
        == "Http404: http://remote/auth/user/receive/"
    )
