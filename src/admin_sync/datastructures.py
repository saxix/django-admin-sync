from dataclasses import asdict, dataclass
from json import JSONEncoder
from typing import Any

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse


@dataclass
class SerializationResult:
    message: str = "success"
    status: int = 200
    details: str = ""
    size: int = -1
    records: int = -1
    payload: str = ""

    as_dict = asdict


@dataclass
class AdminSyncReceiveResult:
    message: str = "success"
    status: int = 200
    details: str = ""
    size: int = -1
    records: int = -1

    as_dict = asdict


@dataclass
class AdminSyncReplyResult:
    message: str = "success"
    details: str = ""
    status: int = 200
    payload: str = ""
    size: int = -1

    as_dict = asdict


class AdminSyncPullDataResponse(JsonResponse):
    """Response sent by reply() view in response of sync_pull_data() trigger."""

    data: SerializationResult

    def __init__(
        self,
        data: SerializationResult,
        encoder: type[JSONEncoder] = DjangoJSONEncoder,
        safe: bool = True,
        json_dumps_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(data.as_dict(), encoder=encoder, safe=safe, json_dumps_params=json_dumps_params, **kwargs)


class AdminSyncPushDataResponse(JsonResponse):
    """Response sent by receive() view in response of sync_publish() trigger."""

    data: AdminSyncReceiveResult

    def __init__(
        self,
        data: AdminSyncReceiveResult,
        encoder: type[JSONEncoder] = DjangoJSONEncoder,
        safe: bool = True,
        json_dumps_params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(data.as_dict(), encoder=encoder, safe=safe, json_dumps_params=json_dumps_params, **kwargs)
