import abc
import io
import logging
import tempfile
from pprint import pprint

import reversion
from concurrency.api import disable_concurrency
from pathlib import Path
from typing import Iterable, Optional, List, Union, Any

from django.core.management import call_command
from django.core.serializers import get_serializer
from django.http import HttpRequest
from django.core.serializers.json import Serializer as JsonSerializer, Deserializer as JsonDeserializer
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
    def serialize(self, data: Iterable):
        c = ForeignKeysCollector(True)
        c.collect(data)
        json: JsonSerializer = get_serializer("json")()
        return json.serialize(
            c.data, use_natural_foreign_keys=True, use_natural_primary_keys=True, indent=3
        )

    def deserialize(self, payload: str) -> list[list[Union[str, Any]]]:
        objects = JsonDeserializer(
            payload,
            ignorenonexistent=True,
            handle_forward_references=True,
        )
        processed = []
        for obj in objects:
            if not obj.deferred_fields:
                obj.save()
        objects = JsonDeserializer(
            payload,
            ignorenonexistent=True,
            handle_forward_references=True,
        )
        for obj in objects:
            processed.append([obj.object._meta.object_name, str(obj.object.pk), obj.object])
            obj.save()
        return processed
