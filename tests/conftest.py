import os
import sys
from pathlib import Path

import pytest
from demoapp.factories import UserFactory


def pytest_configure(config):
    os.environ["DEBUG"] = "False"
    here = Path(__file__).parent
    sys.path.insert(0, str(here / "demo"))
    sys.path.insert(0, str(here.parent / "src"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "demo.settings"


@pytest.fixture(autouse=True)
def setup(settings):
    settings.AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
    settings.ADMIN_SYNC_REMOTE_SERVER = "http://remote"
    settings.DATABASE_NAME = "tests.sqlite"


@pytest.fixture
def app(django_app_factory):
    def get_url_by_id(self, res, object_id):
        for frm in res.forms.values():
            if frm.id == object_id:
                return frm
        raise ValueError("Form id=%s not found" % object_id)

    ret = django_app_factory(csrf_checks=False)
    ret.get_url_by_id = get_url_by_id.__get__(ret)
    return ret


@pytest.fixture
def user(db):
    return UserFactory()
