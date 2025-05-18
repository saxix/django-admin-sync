from django.contrib.auth.models import User

from admin_sync.templatetags.admin_sync import admin_url, classname, remote_url


def test_classname() -> None:
    assert classname(User()) == "User"


def test_admin_url() -> None:
    assert admin_url(User(pk=1), "change") == "/auth/user/1/change/"


def test_remote_url() -> None:
    assert remote_url(User(pk=1), "change") == "http://remote/auth/user/1/change/"
