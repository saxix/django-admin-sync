from __future__ import annotations

from unittest.mock import Mock

import pytest
from django.contrib.auth.models import User

from admin_sync.exceptions import ProtocolError
from admin_sync.protocol import LoadDumpProtocol


def test_protocol_serialize(admin_user):
    p = LoadDumpProtocol(Mock())
    origin = User.objects.all()
    data1 = p.serialize(origin)
    p.deserialize(data1)


def test_protocol_error(admin_user):
    p = LoadDumpProtocol(Mock())
    with pytest.raises(ProtocolError) as e:
        p.deserialize(22)
    assert str(e.value) == "ProtocolError: 'int' object has no attribute 'read'"
