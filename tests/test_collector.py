from demoapp.factories import BaseFactory, DetailFactory, ExtraFactory, UserFactory, user_grant_permissions
from django.contrib.auth.models import Group, User
from django_factory_boy.auth import PermissionFactory

from admin_sync.collector import ForeignKeysCollector


def test_collector(db):
    from demoapp.factories import DetailFactory  # noqa: PLC0415

    d = DetailFactory(
        base__parent__parent=None,
        brother__brother=None,
        brother__base__parent=None,
    )
    c = ForeignKeysCollector(False)
    c.collect([d])
    assert c.data == (
        [d, d.base]
        + [d.base.parent]
        + list(d.base.parent.tags.all())
        + list(d.base.tags.all())
        + [d.brother]
        + [d.brother.base]
        + list(d.brother.base.tags.all())
        + [d.brother.extra]
        + [d.extra]
    )


def test_collector_traverse(db):
    from demoapp.factories import BaseFactory, DetailFactory  # noqa: PLC0415

    b = BaseFactory(parent=None)
    d = DetailFactory(
        base=b,
        base__parent__parent=None,
        brother__brother=None,
        brother__base__parent=None,
    )
    c = ForeignKeysCollector(True)
    c.collect([b])
    assert c.data == ([b, d] + list(b.tags.all()))


def test_collector_common_parent(db):
    from demoapp.factories import BaseFactory, DetailFactory  # noqa: PLC0415

    b = BaseFactory(parent=None)
    d1 = DetailFactory(base=b, extra=None, brother=None)
    d2 = DetailFactory(base=b, extra=None, brother=None)
    c = ForeignKeysCollector(True)
    c.collect([b])
    assert c.data == [b, d1, d2] + list(b.tags.all())


def test_collector_o2o(db):
    from demoapp.factories import BaseFactory, DetailFactory  # noqa: PLC0415

    b = BaseFactory(parent=None)
    d0 = DetailFactory(base=b, extra=None, brother=None)
    d1 = DetailFactory(base=b, extra=None, brother=None)
    d2 = DetailFactory(base=b, brother=d1, extra=None)
    c = ForeignKeysCollector(True)
    c.collect([b, d1, d1])
    assert c.data == [b, d0, d1, d2] + list(b.tags.all())


def test_collector_qs(db):
    from demoapp.factories import GroupFactory, UserFactory  # noqa: PLC0415

    u = UserFactory()
    g = GroupFactory()
    u.groups.add(g)
    c = ForeignKeysCollector(True)
    c.collect(User.objects.all())

    assert c.data == [u, g]


def test_collector_add(db):
    from demoapp.factories import GroupFactory, UserFactory  # noqa: PLC0415

    u = UserFactory()
    g = GroupFactory()
    PermissionFactory()
    u.groups.add(g)
    c = ForeignKeysCollector(True)
    c.collect(User.objects.all())
    c.add(Group.objects.all(), True)
    c.add(Group.objects.all(), None)

    assert c.data == [u, g]


def test_collector_collect(db):
    u = UserFactory()
    c = ForeignKeysCollector()
    c.collect([u])
    assert len(c.data) == 1
    with user_grant_permissions(u, "auth.add_user") as p2:
        c.collect([u], True)
        assert c.data[0:2] == [u, p2.group]
        assert len(c.data) == 7  #  [User, Group, Permission, ContentType, Permission, Permission, Permission]


def test_collector_collect_related(db):
    b = BaseFactory(parent=None, tags=None)
    d = DetailFactory(
        base=b,
        extra=ExtraFactory(),
        brother=None,
    )
    c = ForeignKeysCollector()
    c.collect([d])
    assert c.data[0:2] == [d, b]
    assert len(c.data) == 4  #   [Detail, Base, Extra]
