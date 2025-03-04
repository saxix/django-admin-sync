from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from .conf import ADMIN_SYNC_CONFIG, config


def panel_admin_sync(admin_site: AdminSite, request: HttpRequest) -> HttpResponse:
    context = admin_site.each_context(request)
    credentials = config.get_credentials(request)
    if "logout" in request.GET:
        response = HttpResponseRedirect(".")
        response.delete_cookie(config.CREDENTIALS_COOKIE)
        return response
    context["config"] = ADMIN_SYNC_CONFIG
    context["conf"] = config
    context["remote_logout"] = "."
    context["credentials"] = credentials
    return render(request, "admin/admin_sync/smart_panel.html", context)


panel_admin_sync.verbose_name = _("Admin Sync")
