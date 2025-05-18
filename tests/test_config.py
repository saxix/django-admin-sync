from unittest.mock import Mock

import pytest
from constance.test import override_config

from admin_sync.conf import DjangoConstance, DjangoSettings


def test_settings_config(settings) -> None:
    settings.ADMIN_SYNC_REMOTE_SERVER = "http://localhost:1234"
    c = DjangoSettings()
    assert c.REMOTE_SERVER == "http://localhost:1234"
    assert len(c)
    assert set(c)
    with pytest.raises(AttributeError):
        assert c.INVALID


def test_settings_credentials() -> None:
    c = DjangoSettings()
    assert c.get_credentials(Mock())


@override_config(ADMIN_SYNC_REMOTE_SERVER="http://localhost:8888")
def test_constance_config(db) -> None:
    c = DjangoConstance()
    assert c.REMOTE_SERVER == "http://localhost:8888"
    assert len(c)
    assert set(c)
    with pytest.raises(AttributeError):
        assert c.INVALID
