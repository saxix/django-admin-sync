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
def remote(responses):
    def _get(request):
        client = Client()
        headers = {f"HTTP_{k.upper()}": v for k, v in request.headers.items()}
        ret = client.get(request.path_url, **headers)
        return ret.status_code, ret.headers, ret.content

    def _post(request):
        client = Client()
        headers = {f"HTTP_{k.upper()}": v for k, v in request.headers.items()}
        ret = client.post(request.path_url, **headers)
        return ret.status_code, ret.headers, ret.content

    responses.assert_all_requests_are_fired = False
    responses.add_callback(responses.GET, re.compile(r"http://remote/.*"), _get)
    responses.add_callback(responses.POST, re.compile(r"http://remote/.*"), _post)
    return responses


@pytest.fixture
def app(django_app_factory):
    return django_app_factory(csrf_checks=False)
