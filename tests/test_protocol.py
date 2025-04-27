from unittest.mock import Mock

from django.contrib.auth.models import User

from admin_sync.protocol import LoadDumpProtocol


def test_sync(admin_user):
    p = LoadDumpProtocol(Mock())
    origin = User.objects.all()
    data1 = p.serialize(origin)
    p.deserialize(data1)
