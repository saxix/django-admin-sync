import abc
import logging
import reversion
from typing import Any, Iterable, List, Optional, Union

from django.core.serializers import get_serializer
from django.core.serializers.base import DeserializationError
from django.core.serializers.json import (
    Deserializer as JsonDeserializer,
    Serializer as JsonSerializer,
)
from django.db import transaction, connections
from django.http import HttpRequest

from .collector import BaseCollector
from .exceptions import ProtocolError
from .collector import ForeignKeysCollector, BaseCollector
from .utils import get_client_ip

logger = logging.getLogger(__name__)


class BaseProtocol(abc.ABC):
    collector_class: BaseCollector = ForeignKeysCollector

    def __init__(self, request: Optional[HttpRequest] = None):
        self.request = request

    @abc.abstractmethod
    def serialize(self, collection: Iterable):
        pass

    @abc.abstractmethod
    def deserialize(self, request: HttpRequest):
        pass

    @abc.abstractmethod
    def collect(self, data):
        pass

class ReversionMixin:
    @reversion.create_revision()
    def deserialize(self, payload: str):
        super(ReversionMixin, self).deserialize(payload)


class LoadDumpProtocol(BaseProtocol):
    using = "default"
    def collect(self, data):
        c = self.collector_class(True)
        c.collect(data)
        return c.data

    def serialize(self, data: Iterable):
        data = self.collect(data)
        json: JsonSerializer = get_serializer("json")()
        return json.serialize(
            data,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            indent=3,
        )

    def deserialize(self, payload: str) -> list[list[Union[str, Any]]]:
        processed = []
        try:
            connection = connections[self.using]
            with connection.constraint_checks_disabled():
                with transaction.atomic(self.using):
                    objects = JsonDeserializer(
                            payload,
                            ignorenonexistent=True,
                            handle_forward_references=True,
                        )
                    for obj in objects:
                        obj.save(using=self.using)
                        processed.append(
                            [obj.object._meta.object_name, str(obj.object.pk), str(obj.object)]
                        )
        except DeserializationError as e:
            logger.exception(e)
            raise ProtocolError(e)
        except Exception as e:
            logger.exception(e)
            raise ProtocolError(e)
        return processed
