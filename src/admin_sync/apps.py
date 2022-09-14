from django.contrib.admin.apps import AppConfig


class Config(AppConfig):
    name = "admin_sync"

    def ready(self):
        from . import checks  # noqa
