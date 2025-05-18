from contextlib import ContextDecorator

import factory.django
from django.contrib.auth.models import Group, Permission, User

from .models import Base, Detail, Extra, Tag


class GroupFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Group{n}")

    class Meta:
        model = Group
        django_get_or_create = ("name",)


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"user{n}")

    class Meta:
        model = User
        django_get_or_create = ("username",)


class BaseFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Base %03d" % n)
    parent = factory.SubFactory("demoapp.factories.BaseFactory")

    class Meta:
        model = Base
        django_get_or_create = ("name",)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for group in extracted:
                self.tags.add(group)
        else:
            self.tags.add(TagFactory())


class ExtraFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Extra %03d" % n)

    class Meta:
        model = Extra
        django_get_or_create = ("name",)


class DetailFactory(factory.django.DjangoModelFactory):
    base = factory.SubFactory(BaseFactory)
    name = factory.Sequence(lambda n: "Detail %03d" % n)
    brother = factory.SubFactory("demoapp.factories.DetailFactory")
    extra = factory.SubFactory("demoapp.factories.ExtraFactory")

    class Meta:
        model = Detail
        django_get_or_create = ("name",)


class TagFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Tag %03d" % n)

    class Meta:
        model = Tag
        django_get_or_create = ("name",)


def get_group(name=None, permissions=None):
    group = GroupFactory()
    permission_names = permissions or []
    for permission_name in permission_names:
        try:
            app_label, codename = permission_name.split(".")
        except ValueError:
            raise ValueError("Invalid permission name `{0}`".format(permission_name)) from None
        try:
            permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
        except Permission.DoesNotExist:
            raise Permission.DoesNotExist("Permission `{0}` does not exists", permission_name) from None

        group.permissions.add(permission)
    return group


class user_grant_permissions(ContextDecorator):  # noqa
    caches = [
        "_group_perm_cache",
        "_user_perm_cache",
        "_dsspermissionchecker",
        "_officepermissionchecker",
        "_perm_cache",
        "_dss_acl_cache",
    ]

    def __init__(self, user, permissions=None):
        self.user = user
        if permissions is None:
            permissions = []
        elif not isinstance(permissions, (list, tuple)):
            permissions = [permissions]
        self.permissions = permissions
        self.group = None

    def __enter__(self):
        for cache in self.caches:
            if hasattr(self.user, cache):
                delattr(self.user, cache)
        self.group = get_group(permissions=self.permissions or [])
        self.user.groups.add(self.group)
        return self

    def __exit__(self, e_typ, e_val, trcbak):
        if self.group:
            self.user.groups.remove(self.group)
            self.group.delete()

        if e_typ:
            raise e_typ(e_val).with_traceback(trcbak)

    def start(self):
        """Activate a patch, returning any created mock."""
        return self.__enter__()

    def stop(self):
        """Stop an active patch."""
        return self.__exit__(None, None, None)
