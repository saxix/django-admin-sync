import json
import pytest as pytest
from freezegun import freeze_time

from django.http import HttpResponse

from admin_sync.utils import (
    get_client_ip,
    is_logged_to_remote,
    remote_reverse,
    render,
    set_cookie,
    unwrap,
    wraps,
)

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


def test_unwrap():
    source = json.dumps({"a": 1})
    assert unwrap(wraps(source)) == source


def test_remote_reverse():
    assert remote_reverse("admin:login") == "http://remote/login/"


@freeze_time("2012-01-14 10:10:10")
@pytest.mark.parametrize("expire", [None, 365])
def test_set_cookie(expire):
    response = HttpResponse()
    set_cookie(response, "test", "abc", days_expire=expire)
    assert response.cookies["test"] == {
        "comment": "",
        "domain": "",
        "expires": "Sun, 13-Jan-2013 10:10:10 GMT",
        "httponly": "",
        "max-age": 31536000,
        "path": "/",
        "samesite": "",
        "secure": "",
        "version": "",
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("HTTP_X_ORIGINAL_FORWARDED_FOR", "127.0.0.11"),
        ("HTTP_X_FORWARDED_FOR", "127.0.0.12"),
        ("HTTP_X_REAL_IP", "127.0.0.13"),
        ("REMOTE_ADDR", "127.0.0.14"),
        ("", None),
    ],
)
def test_get_client_ip(rf, key, value):
    request = rf.get("/", **{key: value})
    if key != "REMOTE_ADDR":
        del request.META["REMOTE_ADDR"]
    assert get_client_ip(request) == value


def test_is_logged_to_remote(rf):
    request = rf.get("/")
    assert not is_logged_to_remote(request)


#
# def test_get_prod_credentials(rf):
#     request = rf.get("/")
#     assert get_remote_credentials(request) == {"username": "", "password": ""}
#
#
# def test_get_signed_credentials2(rf):
#     v = sign_prod_credentials("u", "p")
#     request = rf.get("/")
#     request.COOKIES[config.CREDENTIALS_COOKIE] = v
#     assert get_remote_credentials(request) == {"username": "u", "password": "p"}


def test_render(rf):
    request = rf.get("/")
    assert render(request, "admin/base.html", cookies={"a": 1})


#
# def test_get_remote_data_200(admin_user, remote):
#     from django.contrib.auth.models import User
#     url = remote_reverse(admin_urlname(User._meta, "dumpdata_qs"))
#     ret = get_remote_data(url, {"username": admin_user.username,
#                                 "password": "password"})
#     assert json.loads(ret)
#
#
# def test_get_remote_data_403(admin_user, remote):
#     from django.contrib.auth.models import User
#     url = remote_reverse(admin_urlname(User._meta, "dumpdata_qs"))
#     with pytest.raises(PermissionError):
#         assert get_remote_data(url)


# def test_get_remote_data_404(admin_user, responses):
#     url = f"{config.REMOTE_SERVER}/admin/auth/group/dumpdata_qs/"
#     responses.add(responses.GET, url, status=404)
#     with pytest.raises(Http404):
#         get_remote_data(url, {"username": admin_user.username,
#                               "password": "password"})
#
#
# def test_get_remote_data_error(admin_user, responses):
#     url = f"{config.REMOTE_SERVER}/admin/auth/group/dumpdata_qs/"
#     responses.add(responses.GET, url, "", status=200)
#     with pytest.raises(Exception):
#         get_remote_data(url)
#
#
# def test_loaddata_from_url(rf, admin_user, responses):
#     from django.contrib.auth.models import User
#     url = remote_reverse(admin_urlname(User._meta, "dumpdata_qs"))
#     request = rf.get("/")
#     request.user = admin_user
#     responses.add(responses.GET, url, DATA, status=200)
#     loaddata_from_url(request, url)
