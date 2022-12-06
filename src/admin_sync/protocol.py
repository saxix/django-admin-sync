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
from django.http import HttpRequest

from .exceptions import ProtocolError
from .utils import ForeignKeysCollector, get_client_ip

logger = logging.getLogger(__name__)


class BaseProtocol(abc.ABC):
    def __init__(self, request: Optional[HttpRequest] = None):
        self.request = request

    @abc.abstractmethod
    def serialize(self, collection: Iterable):
        pass

    @abc.abstractmethod
    def deserialize(self, request: HttpRequest):
        pass


class ReversionMixin:
    @reversion.create_revision()
    def deserialize(self, payload: str):
        super(ReversionMixin, self).deserialize(payload)


class LoadDumpProtocol(BaseProtocol):
    def serialize(self, data: Iterable, collect_related=True):
        c = ForeignKeysCollector(collect_related)
        c.collect(data)
        json: JsonSerializer = get_serializer("json")()
        return json.serialize(
            c.data,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            indent=3,
        )

    def deserialize(self, payload: str) -> list[list[Union[str, Any]]]:
        try:
            objects = JsonDeserializer(
                payload,
                ignorenonexistent=True,
                handle_forward_references=True,
            )
            processed = []
            for obj in objects:
                if not obj.deferred_fields:
                    try:
                        obj.save()
                    except:
                        pass
            objects = JsonDeserializer(
                payload,
                ignorenonexistent=True,
                handle_forward_references=True,
            )
            for obj in objects:
                processed.append(
                    [obj.object._meta.object_name, str(obj.object.pk), str(obj.object)]
                )
                obj.save()
        except DeserializationError as e:
            raise ProtocolError(e)
        except Exception as e:
            raise ProtocolError(str(e))
        return processed
