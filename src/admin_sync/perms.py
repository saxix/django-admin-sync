from admin_extra_buttons.handlers import BaseExtraHandler
from django.db.models import Model
from django.http import HttpRequest


def check_publish_permission(request: HttpRequest, obj: Model, handler: BaseExtraHandler) -> bool:
    return handler.model_admin.can_publish(request, obj)
