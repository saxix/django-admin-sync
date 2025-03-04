from typing import Any

from django.apps import AppConfig, apps
from django.core.checks import Error, register


@register()
def check_admin_sync_settings(app_configs: AppConfig, **kwargs: Any) -> list[Error]:  # noqa: ARG001
    errors = []
    from .conf import config  # noqa: PLC0415

    if config.USE_REVERSION and not apps.is_installed("reversion"):
        errors.append(
            Error(
                "You have admin-sync configured to use reversion, but reversion is not in your INSTALLED_APPS",
                hint='Either add "reversion" to your settings.INSTALLED_APPS or set ADMIN_SYNC_USE_REVERSION=False',
                obj="admin-sync.Config",
                id="admin-sync.E001",
            )
        )
    return errors
