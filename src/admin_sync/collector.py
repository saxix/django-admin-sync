from __future__ import annotations

import abc
import logging
from itertools import chain
from typing import TYPE_CHECKING

from django.db.models import (
    Field,
    ForeignKey,
    ForeignObjectRel,
    ManyToManyField,
    Model,
    OneToOneField,
    OneToOneRel,
    QuerySet,
)

if TYPE_CHECKING:
    from natural_keys import NaturalKeyModel

logger = logging.getLogger(__name__)


class BaseCollector(abc.ABC):
    def __init__(self, collect_related: bool = True) -> None:
        self.data: list[Model] | None = None
        self.cache = {}
        self.models: set[Model] = set()
        self._visited: list[Model] = []
        self.collect_related: bool = collect_related
        super().__init__()

    @abc.abstractmethod
    def collect(self, objs: list[Model], collect_related: bool = False) -> None: ...  # pragma: no cover

    @abc.abstractmethod
    def add(self, objs: list[Model], collect_related: bool = False) -> None: ...  # pragma: no cover


class ForeignKeysCollector(BaseCollector):
    def get_related_for_field(self, obj: Model, field: "ForeignObjectRel") -> QuerySet[Model] | list[Model]:  # noqa: PLR6301
        try:
            if field.related_name:
                related_attr = getattr(obj, field.related_name)
            elif isinstance(field, OneToOneField | OneToOneRel):
                related_attr = getattr(obj, field.name)
            else:
                related_attr = getattr(obj, f"{field.name}_set")

            if hasattr(related_attr, "all") and callable(related_attr.all):
                related = related_attr.all()
            else:
                related = [related_attr]
        except AttributeError:  # pragma: no cover
            return []
        except Exception as e:  # pragma: no cover
            logger.exception(e)
            raise
        return related

    def get_fields(self, obj: Model) -> list[Field]:
        if obj.__class__ not in self.cache:
            reverse_relations = [f for f in obj._meta.get_fields() if f.auto_created and not f.concrete]
            self.cache[obj.__class__] = reverse_relations
        return self.cache[obj.__class__]

    def get_related_objects(self, obj: Model) -> list[Model]:
        linked = []
        for f in self.get_fields(obj):
            info = self.get_related_for_field(obj, f)
            linked.extend(info)
        return linked

    def visit(self, objs: list[Model]) -> list[Model]:
        added = []
        for o in objs:
            if o not in self._visited:
                self._visited.append(o)
                added.append(o)
        return added

    def _collect(self, objs: list[Model]) -> list[Model]:
        objects = []
        for o in objs:
            if o:
                concrete_model = o._meta.concrete_model
                obj = concrete_model.objects.get(pk=o.pk)
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
                            for t in target:
                                objects.extend(self._collect([t]))
                        elif isinstance(field, ForeignKey):
                            target = getattr(obj, field.name)
                            objects.extend(self._collect([target]))

        return objects

    def add(self, objs: list[Model], collect_related: bool | None = None) -> None:
        if collect_related is not None:
            self.collect_related = collect_related
        self.data += self._collect(objs)

    def collect(self, objs: list[NaturalKeyModel] | QuerySet[Model], collect_related: bool | None = None) -> None:
        if collect_related is not None:
            self.collect_related = collect_related
        self.cache = {}
        self._visited = []
        self.data = self._collect(objs)
