import logging

from django.conf import settings
from django.utils.functional import SimpleLazyObject, cached_property
from django.utils.module_loading import import_string

ADMIN_SYNC_CONFIG = getattr(
    settings, "ADMIN_SYNC_CONFIG", "admin_sync.conf.DjangoSettings"
)

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "1.0"


class Config:
    defaults = dict(
        REMOTE_SERVER="http://localhost:8001",
        DEBUG=settings.DEBUG,
        LOCAL_ADMIN_URL="/admin/",
        REMOTE_ADMIN_URL="/admin/",
        CREDENTIALS_COOKIE="admin_sync_token",
        CREDENTIALS_HOLDER="admin_sync.utils.get_remote_credentials",
        CREDENTIALS_PROMPT=True,
        USE_REVERSION=True,
        RESPONSE_HEADER="x-admin-sync",
    )
    storage = None

    def __init__(self) -> None:
        super().__init__()
        from django.core.signals import setting_changed

        setting_changed.connect(self.on_setting_changed)

    def __iter__(self):
        return iter([[k, getattr(self, k)] for k in self.defaults.keys()])

    def __len__(self):
        return len(self.defaults)

    def _get(self, key):
        if key in self.defaults.keys():
            full_name = f"ADMIN_SYNC_{key}"
            return getattr(self.storage, full_name, self.defaults.get(key, None))

    def get_credentials(self, request):
        f = import_string(self.CREDENTIALS_HOLDER)
        return f(request)

    def __getattr__(self, key):
        if key in self.defaults.keys():
            return self._get(key)
        raise AttributeError(key)

    def on_setting_changed(self, **kwargs):
        self.invalidate()

    def invalidate(self):
        for attr in self.defaults.keys():
            try:
                delattr(self, attr)
            except AttributeError:
                pass


class DjangoSettings(Config):
    storage = settings


class DjangoConstance(DjangoSettings):
    def _get(self, key):
        if key in self.defaults.keys():
            full_name = f"ADMIN_SYNC_{key}"
            return getattr(
                self.storage,
                full_name,
                getattr(settings, full_name, self.defaults.get(key, None)),
            )

    @cached_property
    def storage(self):
        import constance

        return constance.config


def get_config():
    return import_string(ADMIN_SYNC_CONFIG)()


config = SimpleLazyObject(get_config)
