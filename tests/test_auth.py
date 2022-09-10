from django.urls import reverse


def test_get_from_remote_auth(db, django_app, admin_user, remote):
    url = reverse("admin:auth_user_get_qs_from_remote")
    res = django_app.get(url, user=admin_user)
    assert res.status_code == 302
    assert (
        res.headers["location"]
        == "/auth/user/remote_login/?from=%2Fauth%2Fuser%2Fget_qs_from_remote%2F"
    )


def test_login(db, django_app, admin_user, remote):
    url = reverse("admin:auth_user_remote_login")
    res = django_app.get(url, user=admin_user)
    assert res.status_code == 200
    res.forms[1]["username"] = admin_user.username
    res.forms[1]["password"] = admin_user.password
    res = res.forms[1].submit()
    assert res.status_code == 200


def test_logout(db, django_app, admin_user, remote):
    url = reverse("admin:auth_user_remote_logout")
    res = django_app.get(url, user=admin_user)
    assert res.status_code == 302
    assert res.headers["location"] == "http://testserver/auth/user/"
