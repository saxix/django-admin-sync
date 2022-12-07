import abc
from itertools import chain

import logging
from django.db.models import OneToOneField, OneToOneRel, ManyToManyField, ForeignKey

logger = logging.getLogger(__name__)


class BaseCollector(abc.ABC):
    def __init__(self, collect_related=True):
        self.data = None
        self.cache = {}
        self.models = set()
        self._visited = []
        self.collect_related = collect_related
        super().__init__()

    @abc.abstractmethod
    def collect(self, objs, collect_related=None):
        pass

    @abc.abstractmethod
    def add(self, objs, collect_related=None):
        pass


class ForeignKeysCollector(BaseCollector):

    def get_related_for_field(self, obj, field):
        try:
            if field.related_name:
                related_attr = getattr(obj, field.related_name)
            elif isinstance(field, (OneToOneField, OneToOneRel)):
                related_attr = getattr(obj, field.name)
            else:
                related_attr = getattr(obj, f"{field.name}_set")

            if hasattr(related_attr, "all") and callable(related_attr.all):
                related = related_attr.all()
            else:
                related = [related_attr]
        except AttributeError as e:  # pragma: no cover
            return []
        except Exception as e:  # pragma: no cover
            logger.exception(e)
            raise
        return related

    def get_fields(self, obj):
        if obj.__class__ not in self.cache:
            reverse_relations = []
            for f in obj._meta.get_fields():
                if f.auto_created and not f.concrete:
                    reverse_relations.append(f)
            self.cache[obj.__class__] = reverse_relations
        return self.cache[obj.__class__]

    def get_related_objects(self, obj):
        linked = []
        for f in self.get_fields(obj):
            info = self.get_related_for_field(obj, f)
            linked.extend(info)
        return linked

    def visit(self, objs):
        added = []
        for o in objs:
            if o not in self._visited:
                self._visited.append(o)
                added.append(o)
        return added

    def _collect(self, objs):
        objects = []
        for obj in objs:
            if obj:
                concrete_model = obj._meta.concrete_model
                obj = concrete_model.objects.get(pk=obj.pk)
                opts = obj._meta
                self.get_fields(obj)
                if obj not in self._visited:
                    self._visited.append(obj)
                    objects.append(obj)
                    if self.collect_related:
                        related = self.get_related_objects(obj)
                        objects.extend(self.visit(related))
                    for field in chain(opts.fields, opts.many_to_many):
                        if isinstance(field, ManyToManyField):
                            target = getattr(obj, field.name).all()
                            for o in target:
                                objects.extend(self._collect([o]))
                        elif isinstance(field, ForeignKey):
                            target = getattr(obj, field.name)
                            objects.extend(self._collect([target]))

        return objects

    def add(self, objs, collect_related=None):
        if collect_related is not None:
            self.collect_related = collect_related
        self.data += self._collect(objs)

    def collect(self, objs, collect_related=None):
        if collect_related is not None:
            self.collect_related = collect_related
        self.cache = {}
        self._visited = []
        self.data = self._collect(objs)
        # self.models = [o.__name__ for o in self.cache.keys()]
