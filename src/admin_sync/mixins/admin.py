from __future__ import annotations

import logging

from admin_extra_buttons.decorators import button, view
from django.contrib import admin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ..perms import check_publish_permission
from .publish import PublishMixin
from .receiver import ReceiveMixin

logger = logging.getLogger(__name__)


class SyncMixin(PublishMixin, ReceiveMixin):
    @button(permission=check_publish_permission)  # type: ignore[arg-type]
    def publish(self, request, pk):
        return self._publish(request, pk)

    @view(decorators=[csrf_exempt], http_basic_auth=False, login_required=False)  # type: ignore[arg-type]
    def receive(self, request) -> JsonResponse:
        response = self._receive(request)
        return JsonResponse(response.as_dict(), status=response.code)


class SyncModelAdmin(SyncMixin, admin.ModelAdmin):
    pass
