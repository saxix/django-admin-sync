from admin_sync.collector import ForeignKeysCollector


def test_collector(db):
    from demoapp.factories import DetailFactory

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
    from demoapp.factories import BaseFactory, DetailFactory

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
    from demoapp.factories import BaseFactory, DetailFactory

    b = BaseFactory(parent=None)
    d1 = DetailFactory(base=b, extra=None, brother=None)
    d2 = DetailFactory(base=b, extra=None, brother=None)
    c = ForeignKeysCollector(True)
    c.collect([b])
    assert c.data == [b, d1, d2] + list(b.tags.all())


def test_collector_o2o(db):
    from demoapp.factories import BaseFactory, DetailFactory

    b = BaseFactory(parent=None)
    d0 = DetailFactory(base=b, extra=None, brother=None)
    d1 = DetailFactory(base=b, extra=None, brother=None)
    d2 = DetailFactory(base=b, brother=d1, extra=None)
    c = ForeignKeysCollector(True)
    c.collect([b, d1, d1])
    assert c.data == [b, d0, d1, d2] + list(b.tags.all())
