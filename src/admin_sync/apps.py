from django.contrib.admin.apps import AppConfig


class Config(AppConfig):
    name = "admin_sync"

    def ready(self):
        from . import checks  # noqa
        from django.apps import apps
        from django.contrib.admin import site
        if apps.is_installed("smart_admin"):
            from .smart_panel import panel_admin_sync
            site.register_panel(panel_admin_sync)

