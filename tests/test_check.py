from demoapp.models import MissingNaturalKey, MissingNaturalKeyProtocol, Tag
from django.contrib.auth.models import User


def test_check(db):
    from demoapp.admin import site

    m1 = site._registry[Tag]
    assert [m.msg for m in m1.check()] == [
        "demoapp.Tag default manager does not implement get_by_natural_key() method."
    ]

    m2 = site._registry[MissingNaturalKeyProtocol]
    assert [m.msg for m in m2.check()] == ["demoapp.MissingNaturalKeyProtocol does not implement NaturalKeys protocol."]

    m3 = site._registry[MissingNaturalKey]
    assert [m.msg for m in m3.check()] == ["demoapp.MissingNaturalKey does not implement natural_key() method."]

    m4 = site._registry[User]
    assert not m4.check()
