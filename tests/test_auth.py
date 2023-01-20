from django.urls import reverse


def test_get_from_remote_auth(db, app, admin_user, remote):
    url = reverse("admin:auth_user_get_qs_from_remote")
    res = app.get(url, user=admin_user)
    assert res.status_code == 302
    assert (
        res.headers["location"]
        == "/auth/user/remote_login/?from=%2Fauth%2Fuser%2Fget_qs_from_remote%2F"
    )


def test_login(db, app, admin_user, remote):
    url = reverse("admin:auth_user_remote_login")
    res = app.get(url, user=admin_user)
    assert res.status_code == 200
    frm = app.get_url_by_id(res, "sync-remote-login")
    frm["username"] = admin_user.username
    frm["password"] = admin_user.password
    res = frm.submit()
    assert res.status_code == 200


def test_logout(db, app, admin_user, remote):
    url = reverse("admin:auth_user_remote_logout")
    res = app.get(url, user=admin_user)
    assert res.status_code == 302
    assert res.headers["location"] == "http://testserver/auth/user/"
