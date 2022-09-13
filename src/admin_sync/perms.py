from django.db.models import Model
from django.http import HttpRequest

from admin_extra_buttons.handlers import BaseExtraHandler


def check_publish_permission(
    request: HttpRequest, obj: Model, handler: BaseExtraHandler, **kwargs
) -> bool:
    return handler.model_admin.check_publish_permission(request, obj)


def check_sync_permission(request, obj, handler: BaseExtraHandler, **kwargs):
    return handler.model_admin.check_sync_permission(request, obj)
