from unittest.mock import Mock

from django.contrib.auth.models import User

from admin_sync.protocol import LoadDumpProtocol


def test_sync(admin_user):
    p = LoadDumpProtocol(Mock())
    origin = User.objects.all()
    data1 = p.serialize(origin)
    data2 = p.deserialize(data1)
    # FIXME: remove me (print)
    print(111, "test_protocol.py:16 (test_sync)", data2)
