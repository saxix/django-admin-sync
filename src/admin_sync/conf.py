import logging

from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.module_loading import import_string

ADMIN_SYNC_CONFIG = getattr(
    settings, "ADMIN_SYNC_CONFIG", "admin_sync.conf.DjangoSettings"
)

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "1.0"

class Config:
    defaults = dict(
        ADMIN_SYNC_REMOTE_SERVER="http://localhost:8001",
        ADMIN_SYNC_LOCAL_ADMIN_URL="/admin/",
        ADMIN_SYNC_REMOTE_ADMIN_URL="/admin/",
        ADMIN_SYNC_CREDENTIALS_COOKIE="admin_sync_token",
        ADMIN_SYNC_GET_CREDENTIALS="admin_sync.utils.get_remote_credentials",
        ADMIN_SYNC_CREDENTIALS_PROMPT=True,
        ADMIN_SYNC_USE_REVERSION=True,
    )
    storage = None

    def __init__(self) -> None:
        super().__init__()
        from django.core.signals import setting_changed

        setting_changed.connect(self.on_setting_changed)

    def _get(self, key):
        return getattr(self.storage, key, self.defaults.get(key, None))

    def __getattr__(self, item):
        if f"ADMIN_SYNC_{item}" in self.defaults.keys():
            return self._get(f"ADMIN_SYNC_{item}")
        raise ValueError(item)

    # @cached_property
    # def REMOTE_SERVER(self):
    #     return self._get("ADMIN_SYNC_REMOTE_SERVER")
    #
    # @cached_property
    # def LOCAL_ADMIN_URL(self):
    #     return self._get("ADMIN_SYNC_LOCAL_ADMIN_URL")
    #
    # @cached_property
    # def REMOTE_ADMIN_URL(self):
    #     return self._get("ADMIN_SYNC_REMOTE_ADMIN_URL")
    #
    # @cached_property
    # def CREDENTIALS_COOKIE(self):
    #     return self._get("ADMIN_SYNC_CREDENTIALS_COOKIE")
    #
    # @cached_property
    # def GET_CREDENTIALS(self):
    #     return self._get("ADMIN_SYNC_GET_CREDENTIALS")
    #
    # @cached_property
    # def CREDENTIALS_PROMPT(self):
    #     return self._get("ADMIN_SYNC_CREDENTIALS_PROMPT")

    def on_setting_changed(self, **kwargs):
        self.invalidate()

    def invalidate(self):
        for attr in [
            "REMOTE_SERVER",
            "CREDENTIALS_COOKIE",
            "REMOTE_ADMIN_URL",
            "LOCAL_ADMIN_URL",
            "GET_CREDENTIALS",
            "CREDENTIALS_PROMPT",
        ]:
            try:
                delattr(self, attr)
            except AttributeError:
                pass


class DjangoSettings(Config):
    storage = settings


def get_config():
    return import_string(ADMIN_SYNC_CONFIG)()


config = SimpleLazyObject(get_config)
