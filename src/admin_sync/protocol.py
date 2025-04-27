from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING, Any

import reversion
from django.core.serializers import get_serializer
from django.core.serializers.base import DeserializationError
from django.core.serializers.json import (
    Deserializer as JsonDeserializer,
)
from django.core.serializers.json import (
    Serializer as JsonSerializer,
)
from django.db import connections, transaction

from .collector import BaseCollector, ForeignKeysCollector
from .exceptions import ProtocolError

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.db.models import Model
    from django.http import HttpRequest

    from .types import Collectable


logger = logging.getLogger(__name__)


class BaseProtocol(abc.ABC):
    collector_class: BaseCollector = ForeignKeysCollector

    def __init__(self, request: HttpRequest | None = None) -> None:
        self.request = request

    @abc.abstractmethod
    def serialize(self, collection: Iterable) -> None:
        pass

    @abc.abstractmethod
    def deserialize(self, request: HttpRequest) -> list[list[Any]]:
        pass

    @abc.abstractmethod
    def collect(self, data: "Collectable") -> Iterable[Model]:
        pass


class ReversionMixin:
    @reversion.create_revision()
    def deserialize(self, payload: str) -> list[list[Any]]:
        return super().deserialize(payload)


class LoadDumpProtocol(BaseProtocol):
    using = "default"

    def collect(self, data: "Collectable") -> Iterable[Model]:
        c = self.collector_class(collect_related=True)
        c.collect(data)
        return c.data

    def serialize(self, data: "Collectable") -> str:
        data = self.collect(data)
        json: JsonSerializer = get_serializer("json")()
        return json.serialize(
            data,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            indent=3,
        )

    def deserialize(self, payload: str) -> list[list[Any]]:
        processed = []
        try:
            connection = connections[self.using]
            with connection.constraint_checks_disabled(), transaction.atomic(self.using):
                objects = JsonDeserializer(
                    payload,
                    ignorenonexistent=True,
                    handle_forward_references=True,
                )
                for obj in objects:
                    obj.save(using=self.using)
                    processed.append(
                        [
                            obj.object._meta.object_name,
                            str(obj.object.pk),
                            str(obj.object),
                        ]
                    )
        except DeserializationError as e:
            logger.exception(e)
            raise ProtocolError(e) from e
        except Exception as e:
            logger.exception(e)
            raise ProtocolError(e) from e
        return processed
