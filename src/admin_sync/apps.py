from django.contrib.admin.apps import AppConfig


class Config(AppConfig):
    name = "admin_sync"

    def ready(self) -> None:  # noqa: PLR6301
        from . import checks  # noqa: PLC0415, F401
