from __future__ import annotations

import logging
from typing import Any

from admin_extra_buttons.decorators import button, view
from django.contrib import admin
from django.core.checks import CheckMessage, Warning as Warn
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..perms import check_publish_permission, check_pull_permission
from .publisher import PublishMixin
from .puller import PullMixin
from .receiver import ReceiveMixin
from .replier import ReplierMixin

logger = logging.getLogger(__name__)


class SyncPushMixin(PublishMixin, ReceiveMixin):
    @button(permission=check_publish_permission)  # type: ignore[arg-type]
    def publish(self, request, pk):
        """Send data To Remote"""
        return self.sync_publish(request, pk)

    @view(decorators=[csrf_exempt], http_basic_auth=False, login_required=False)  # type: ignore[arg-type]
    def receive(self, request) -> JsonResponse:
        """Receive data sent using publish() event"""
        response = self._receive(request)
        return JsonResponse(response.as_dict(), status=response.code)


class SyncPullMixin(PullMixin, ReplierMixin):
    @button(permission=check_pull_permission)  # type: ignore[arg-type]
    def pull(self, request, pk):
        """Pull data from Remote"""
        return self.sync_pull_data(request, pk)

    @view(decorators=[csrf_exempt], http_basic_auth=False, login_required=False)  # type: ignore[arg-type]
    def reply(self, request: HttpRequest, natural_key: str) -> JsonResponse:
        """Respond to a pull request."""
        try:
            response = self._reply(request, natural_key)
            return JsonResponse(response.as_dict(), status=response.code)
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"message": "Unhandled Error", "code": 500}, status=500)


class SyncModelAdmin(SyncPushMixin, SyncPullMixin, admin.ModelAdmin):
    def check(self, **kwargs: Any) -> list[CheckMessage]:
        errors = super().check(**kwargs)
        has_natural_key = hasattr(self.model, "natural_key")
        has_get_by_natural_key = hasattr(self.model._default_manager, "get_by_natural_key")
        model_name = self.model._meta.label
        if not has_get_by_natural_key and not has_natural_key:
            errors.append(
                Warn(
                    f"{model_name} does not implement NaturalKeys protocol.",
                    id="AdminSync.001",
                    hint="see https://docs.djangoproject.com/en/5.2/topics/serialization/#natural-keys",
                    obj=self,
                )
            )
        elif not has_natural_key:
            errors.append(
                Warn(f"{model_name} does not implement natural_key() method.", id="AdminSync.002", hint="", obj=self)
            )
        elif not has_get_by_natural_key:
            errors.append(
                Warn(
                    f"{model_name} default manager does not implement get_by_natural_key() method.",
                    id="AdminSync.003",
                    hint="",
                    obj=self,
                )
            )
        return errors
