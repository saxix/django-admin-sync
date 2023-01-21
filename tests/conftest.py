import os
import pytest
import re

from django.test import Client


def pytest_configure(config):
    os.environ["DEBUG"] = "False"


@pytest.fixture(autouse=True)
def setup(settings):
    settings.AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
    settings.ADMIN_SYNC_REMOTE_SERVER = "http://remote"
    settings.DATABASE_NAME = "tests.sqlite"


@pytest.fixture()
def remote(responses, settings):
    def _get(request):
        settings.SESSION_COOKIE_NAME = "remote"
        client = Client()
        headers = {f"HTTP_{k.upper()}": v for k, v in request.headers.items()}
        ret = client.get(request.path_url, **headers)
        for k, v in ret.headers.items():
            if k == "Set-Cookie":
                ret.headers[k] = v.replace(
                    f" {settings.SESSION_COOKIE_NAME}=", " remote="
                )
            else:
                ret.headers[k] = v.replace("http://testserver", "http://remote")
        return ret.status_code, ret.headers, ret.content

    def _post(request):
        client = Client()
        headers = {f"HTTP_{k.upper()}": v for k, v in request.headers.items()}
        ret = client.post(request.path_url, **headers)
        for k, v in ret.headers.items():
            if k == "Set-Cookie":
                ret.headers[k] = v.replace(
                    f" {settings.SESSION_COOKIE_NAME}=", " remote="
                )
            else:
                ret.headers[k] = v.replace("http://testserver", "http://remote")
        return ret.status_code, ret.headers, ret.content

    responses.assert_all_requests_are_fired = False
    responses.add_callback(responses.GET, re.compile(r"http://remote/.*"), _get)
    responses.add_callback(responses.POST, re.compile(r"http://remote/.*"), _post)
    return responses


@pytest.fixture
def app(django_app_factory):
    def get_url_by_id(self, res, id):
        for idx, frm in res.forms.items():
            if frm.id == id:
                return frm
        raise ValueError("Form id=%s not found" % id)

    ret = django_app_factory(csrf_checks=False)
    ret.get_url_by_id = get_url_by_id.__get__(ret)
    return ret
