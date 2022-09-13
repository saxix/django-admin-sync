import factory.django

from .models import Base, Detail, Extra, Tag


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


class ExtraFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Extra %03d" % n)

    class Meta:
        model = Extra
        django_get_or_create = ("name",)
