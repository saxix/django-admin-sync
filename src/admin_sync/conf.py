from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from django.conf import settings
from django.utils.functional import SimpleLazyObject, cached_property
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from collections.abc import Iterator

    from django.http import HttpRequest


ADMIN_SYNC_CONFIG = getattr(settings, "ADMIN_SYNC_CONFIG", "admin_sync.conf.DjangoSettings")

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "1.0"


class Config:
    defaults: ClassVar = {
        "REMOTE_SERVER": "http://localhost:8001",
        "DEBUG": settings.DEBUG,
        "LOCAL_ADMIN_URL": "/admin/",
        "REMOTE_ADMIN_URL": "/admin/",
        "CREDENTIALS_HOLDER": "admin_sync.utils.get_remote_credentials",
        "REMOTE_PASSWORD": "",
        "REMOTE_USER": "",
        "RESPONSE_HEADER": "x-admin-sync",
    }
    storage = None

    def __iter__(self) -> Iterator[tuple[str, str]]:
        return iter([(k, getattr(self, k)) for k in self.defaults])

    def __len__(self) -> int:
        return len(self.defaults)

    def _get(self, key: str) -> Any:
        full_name = f"ADMIN_SYNC_{key}"
        return getattr(self.storage, full_name, self.defaults.get(key, None))

    def get_credentials(self, request: HttpRequest) -> dict[str, str]:
        f = import_string(self.CREDENTIALS_HOLDER)
        return f(request)

    def __getattr__(self, key: str) -> str | bool:
        if key in self.defaults:
            return self._get(key)
        raise AttributeError(key)


class DjangoSettings(Config):
    storage = settings


class DjangoConstance(DjangoSettings):
    def _get(self, key: str) -> bool | str | None:
        full_name = f"ADMIN_SYNC_{key}"
        return getattr(
            self.storage,
            full_name,
            getattr(settings, full_name, self.defaults.get(key, None)),
        )

    @cached_property
    def storage(self) -> dict[str, Any]:  # noqa: PLR6301
        import constance  # noqa: PLC0415

        return constance.config


def get_config() -> Config:
    return import_string(ADMIN_SYNC_CONFIG)()


config: Config = SimpleLazyObject(get_config)
