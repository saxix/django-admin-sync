from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING, Any, ClassVar, Sized

from django.core.serializers.json import Deserializer as JsonDeserializer
from django.core.serializers.json import Serializer as JsonSerializer
from django.db import connections, transaction

from .collector import BaseCollector, ForeignKeysCollector
from .exceptions import ProtocolError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.core.serializers.base import Deserializer, Serializer
    from django.db.models import Model
    from django.http import HttpRequest

    from .types import Collectable


logger = logging.getLogger(__name__)


class BaseProtocol(abc.ABC):
    collector_class: BaseCollector = ForeignKeysCollector

    def __init__(self, request: HttpRequest | None = None) -> None:
        self.request = request

    @abc.abstractmethod
    def serialize(self, collection: Iterable) -> None: ...

    @abc.abstractmethod
    def deserialize(self, request: HttpRequest) -> list[list[Any]]: ...

    @abc.abstractmethod
    def collect(self, data: "Collectable") -> Iterable[Model]: ...


class LoadDumpProtocol(BaseProtocol):
    using = "default"
    serializer_class: "ClassVar[type[Serializer]]" = JsonSerializer
    deserializer_class: "ClassVar[type[Deserializer]]" = JsonDeserializer

    @property
    def serializer(self) -> "Serializer":
        return self.serializer_class()

    def collect(self, data: "Collectable") -> Sized[Model]:
        c = self.collector_class(collect_related=True)
        c.collect(data)
        return c.data

    def serialize(self, data: Iterable) -> Any:
        data = self.collect(data)
        return self.serializer.serialize(data, use_natural_foreign_keys=True, use_natural_primary_keys=True)

    def deserialize(self, payload: str) -> list[list[Any]]:
        processed = []
        try:
            connection = connections[self.using]
            with connection.constraint_checks_disabled(), transaction.atomic(self.using):
                objects = self.__class__.deserializer_class(
                    stream_or_string=payload, ignorenonexistent=True, handle_forward_references=True
                )
                for obj in objects:
                    obj.save(using=self.using)
                    processed.append([obj.object._meta.object_name, str(obj.object.pk)])
        except AttributeError as e:
            logger.exception(e)
            raise ProtocolError(e) from None
        return processed
