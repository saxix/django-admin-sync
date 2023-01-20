from django.urls import reverse

DATA = (
    '{"data": "%5B%7B%22model%22%3A%20%22auth.user%22%2C%20%22fields%22%3A%20%7B%22'
    "password%22%3A%20%22%22%2C%20%22last_login%22%3A%20%222022-09-05T15%3A17%3A28."
    "017Z%22%2C%20%22is_superuser%22%3A%20true%2C%20%22username%22%3A%20%22"
    "pippo2%22%2C%20%22first_name%22%3A%20%22%22%2C%20%22last_name%22%3A%20%22%22%2C%20%22"
    "email%22%3A%20%22pippo2%40demo.org%22%2C%20%22is_staff%22%3A%20true%2C%20%22"
    "is_active%22%3A%20true%2C%20%22date_joined%22%3A%20%222022-09-05T15%3A17%3A28.009Z%22%2C%20%22"
    "groups%22%3A%20%5B%5D%2C%20%22user_permissions%22%3A%20%5B%5D%7D%7D%2C%20%7B%22"
    "model%22%3A%20%22auth.user%22%2C%20%22fields%22%3A%20%7B%22password%22%3A%20%22%22%2C%20%22"
    "last_login%22%3A%20%222022-09-05T15%3A23%3A41.500Z%22%2C%20%22is_superuser%22%3A%20true%2C%20%22"
    "username%22%3A%20%22sss%22%2C%20%22first_name%22%3A%20%22%22%2C%20%22"
    "last_name%22%3A%20%22%22%2C%20%22email%22%3A%20%22sss%40demo.org%22%2C%20%22"
    "is_staff%22%3A%20true%2C%20%22is_active%22%3A%20true%2C%20%22"
    "date_joined%22%3A%20%222022-09-05T15%3A18%3A08.198Z%22%2C%20%22groups%22%3A%20%5B%5D%2C%20%22"
    "user_permissions%22%3A%20%5B%5D%7D%7D%2C%20%7B%22model%22%3A%20%22auth.user%22%2C%20%22"
    "fields%22%3A%20%7B%22password%22%3A%20%22%22%2C%20%22"
    "last_login%22%3A%20%222022-09-06T03%3A40%3A36.060Z%22%2C%20%22is_superuser%22%3A%20"
    "true%2C%20%22username%22%3A%20%22admin%22%2C%20%22first_name%22%3A%20%22%22%2C%20%22"
    "last_name%22%3A%20%22%22%2C%20%22email%22%3A%20%22admin%40demo.org%22%2C%20%22"
    "is_staff%22%3A%20true%2C%20%22is_active%22%3A%20true%2C%20%22"
    "date_joined%22%3A%20%222022-09-06T03%3A31%3A18.124Z%22%2C%20%22groups%22%3A%20%5B%5D%2C%20%22"
    'user_permissions%22%3A%20%5B%5D%7D%7D%5D"}'
)


def test_fetch(app, admin_user, monkeypatch, remote):
    url = reverse("admin:auth_user_changelist")
    res = app.get(url, user=admin_user)
    res = res.click(linkid="btn-get_qs_from_remote").follow()
    frm = app.get_url_by_id(res, "sync-remote-login")
    frm["username"] = admin_user.username
    frm["password"] = "password"
    res = frm.submit().follow()

    frm = app.get_url_by_id(res, "sync-remote-load")
    res = frm.submit()

    assert (
        str(list(res.context["messages"])[0])
        == "Fetching data from http://remote/auth/user/dumpdata_qs/"
    )
    assert str(list(res.context["messages"])[1]) == "Success"
    assert "result" in res.context


def test_sync(app, admin_user, monkeypatch, remote):
    url = reverse("admin:auth_user_change", args=[admin_user.pk])
    res = app.get(url, user=admin_user)
    res = res.click(linkid="btn-sync").follow()
    frm = app.get_url_by_id(res, "sync-remote-login")
    frm["username"] = admin_user.username
    frm["password"] = "password"
    res = frm.submit().follow()

    frm = app.get_url_by_id(res, "sync-remote-fetch")
    res = frm.submit()

    assert (
        str(list(res.context["messages"])[0])
        == "Fetching data from http://remote/auth/user/admin/dumpdata_single/"
    )
    assert str(list(res.context["messages"])[1]) == "Success"
    assert "stdout" in res.context


def test_publish(app, admin_user, responses):
    responses.add(
        responses.POST,
        "http://remote/auth/user/check_login/",
        '{"user": "' + admin_user.username + '"}',
        status=200,
    )
    responses.add(
        responses.POST, "http://remote/auth/user/receive/", '{"user": ""}', status=200
    )

    url = reverse("admin:auth_user_change", args=[admin_user.pk])
    res = app.get(url, user=admin_user)
    res = res.click(linkid="btn-publish").follow()
    frm = app.get_url_by_id(res, "sync-remote-login")
    frm["username"] = admin_user.username
    frm["password"] = "password"
    res = frm.submit().follow()

    frm = app.get_url_by_id(res, "sync-remote-publish")
    res = frm.submit()

    assert str(list(res.context["messages"])[0]) == "Success"


def test_publish_no_auth(app, admin_user, monkeypatch):
    monkeypatch.setattr("admin_sync.mixin.is_logged_to_remote", lambda s: False)
    url = reverse("admin:auth_user_publish", args=[admin_user.pk])
    res = app.get(url, user=admin_user)
    assert (
        res["location"]
        == "/auth/user/remote_login/?from=%2Fauth%2Fuser%2F1%2Fpublish%2F"
    )

    res = app.post(url, user=admin_user, expect_errors=True)
    assert res.status_code == 302
    assert (
        res["location"]
        == "/auth/user/remote_login/?from=%2Fauth%2Fuser%2F1%2Fpublish%2F"
    )


def test_publish_remote_error(app, admin_user, monkeypatch):
    def raise_(*a):
        raise Exception("General Exception")

    monkeypatch.setattr("admin_sync.mixin.PublishMixin.post_data_to_remote", raise_)
    monkeypatch.setattr("admin_sync.mixin.is_logged_to_remote", lambda s: True)
    url = reverse("admin:auth_user_publish", args=[admin_user.pk])
    res = app.post(url, user=admin_user)
    assert str(list(res.context["messages"])[0]) == "Exception: General Exception"


def test_receive(app, admin_user):
    url = reverse("admin:auth_user_receive")
    res = app.post(url, DATA, user=admin_user)
    assert res.json["message"] == "Done"


def test_receive_error(app, admin_user):
    url = reverse("admin:auth_user_receive")
    res = app.post(url, "", user=admin_user, expect_errors=True)
    assert res.status_code == 400
    assert res.json == {
        "error": "Expecting value: line 1 column 1 (char 0)",
    }
