from __future__ import annotations

import json
import logging
from http import HTTPStatus
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any
from urllib.parse import quote_plus, unquote_plus

import requests
from admin_extra_buttons.api import ExtraButtonsMixin, button, view
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core import checks
from django.core.serializers import get_serializer
from django.core.validators import ValidationError
from django.db.models import Model, QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls.base import reverse as local_reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_variables
from requests.auth import HTTPBasicAuth

from .conf import PROTOCOL_VERSION, config
from .exceptions import PublishError, RemoteError, UnsupportedError, VersionMismatchError
from .forms import ProductionLoginForm
from .perms import check_publish_permission, check_sync_permission
from .protocol import BaseProtocol, LoadDumpProtocol
from .signals import (
    admin_sync_data_fetched,
    admin_sync_data_published,
    admin_sync_data_received,
)
from .utils import (
    SyncErrorResponse,
    SyncResponse,
    is_local,
    is_logged_to_remote,
    is_remote,
    remote_reverse,
    render,
    set_cookie,
    sign_prod_credentials,
    unwrap,
    wraps,
)

if TYPE_CHECKING:
    from admin_extra_buttons.buttons import ButtonWidget
    from django.core.serializers.base import Serializer
    from django.db.models.options import Options
    from django.template import Context
    from natural_keys import NaturalKeyModel

logger = logging.getLogger(__name__)


class BaseSyncMixin(ExtraButtonsMixin):
    def post_remote_data(self, request: HttpRequest, url: str, data: dict[str, Any]) -> dict[str, str]:  # noqa: PLR6301
        auth = None
        if credentials := config.get_credentials(request):
            auth = HTTPBasicAuth(**credentials)
        ret = requests.post(url, data=data, auth=auth, timeout=60)
        if ret.status_code == HTTPStatus.BAD_REQUEST:
            raise PublishError(ret)
        if ret.status_code == HTTPStatus.FORBIDDEN:
            raise PermissionError
        if ret.status_code == HTTPStatus.NOT_FOUND:
            raise Http404(url)
        return ret.json()

    @sensitive_variables("credentials")
    def get_remote_data(self, request: HttpRequest, url_name: str, obj: NaturalKeyModel | None = None) -> str:  # noqa: C901
        if obj:
            natural_key = "|".join(obj.natural_key())
            url = remote_reverse(admin_urlname(self.model._meta, url_name), args=[natural_key])
        else:
            url = remote_reverse(admin_urlname(self.model._meta, url_name))
        self.message_user(request, f"Fetching data from {url}", messages.WARNING)
        auth = None
        if credentials := config.get_credentials(request):
            auth = HTTPBasicAuth(**credentials)
        ret = requests.get(url, auth=auth, allow_redirects=False, timeout=60)
        if ret.status_code == HTTPStatus.BAD_REQUEST:
            raise RemoteError(ret.content)
        if ret.status_code == HTTPStatus.FORBIDDEN:
            raise PermissionError
        if ret.status_code == HTTPStatus.NOT_FOUND:
            raise Http404(url)
        if ret.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            raise RemoteError(url)
        if ret.status_code == HTTPStatus.FOUND:
            raise RemoteError(f"Received redirect to '{ret.headers['location']}'")
        ct = ret.headers.get("Content-Type", "")
        if "application/json" not in ct:
            raise RemoteError(f"Received wrong Content-Type: '{ct}'")
        try:
            if config.RESPONSE_HEADER and ret.headers[config.RESPONSE_HEADER] != PROTOCOL_VERSION:
                raise VersionMismatchError("Remote site is using an incompatible protocol.")
            payload = unwrap(ret.content)
        except JSONDecodeError as e:
            logger.exception(e)
            raise JSONDecodeError(f"{ret.status_code}: {ret.content}") from e
        except KeyError as e:
            logger.exception(e)
            raise UnsupportedError from e
        except Exception as e:
            logger.exception(e)
            raise
        return payload


class RemoteLogin(BaseSyncMixin):
    @view(decorators=[csrf_exempt], http_basic_auth=True, enabled=is_remote)
    def check_login(self, request: HttpRequest) -> HttpResponse:  # noqa: PLR6301
        response = JsonResponse({"user": request.user.username})
        set_cookie(response, "editor_logged", "1")
        return response

    @view(decorators=[csrf_exempt], http_basic_auth=True, enabled=is_remote)
    def remote_logout(self, request: HttpRequest) -> HttpResponse:  # noqa: PLR6301
        redir_url = request.build_absolute_uri(unquote_plus(request.GET.get("from", "..")))
        response = HttpResponseRedirect(redir_url)
        response.delete_cookie(config.CREDENTIALS_COOKIE)
        return response

    @view(enabled=is_local)
    def remote_login(self, request: HttpRequest) -> HttpResponse:
        context = self.get_common_context(request, title=f"Login to remote ({config.REMOTE_SERVER})")
        cookies = {}
        if request.method == "POST":
            form = ProductionLoginForm(data=request.POST)
            if form.is_valid():
                try:
                    basic = HTTPBasicAuth(**form.cleaned_data)
                    url = remote_reverse(admin_urlname(self.model._meta, "check_login"))
                    ret = requests.post(url, auth=basic, timeout=60)
                    if ret.status_code == HTTPStatus.OK:
                        data = ret.json()
                        if data["user"] != form.cleaned_data["username"]:
                            raise ValidationError("---")
                        cookies[config.CREDENTIALS_COOKIE] = sign_prod_credentials(**form.cleaned_data)
                        data = ret.json()
                        self.message_user(
                            request,
                            f"Logged in to {config.REMOTE_SERVER} as {data['user']}",
                        )
                        if "from" in request.GET:
                            redir_url = request.build_absolute_uri(unquote_plus(request.GET["from"]))
                            response = HttpResponseRedirect(redir_url)
                            if cookies[config.CREDENTIALS_COOKIE]:
                                response.set_cookie(
                                    config.CREDENTIALS_COOKIE,
                                    cookies[config.CREDENTIALS_COOKIE],
                                )
                            return response
                    else:
                        self.message_user(request, f"Login failed {ret} - {url}", messages.ERROR)
                except Exception as e:
                    logger.exception(e)
                    self.message_error_to_user(request, e)
        else:
            form = ProductionLoginForm()
        context["form"] = form
        context["login_url"] = remote_reverse(admin_urlname(self.model._meta, "check_login"))
        return render(request, "admin/admin_sync/login_prod.html", context, cookies=cookies)

    def get_common_context(self, request: HttpRequest, pk: str | None = None, **kwargs: Any) -> Context:
        opts: Options = self.model._meta
        kwargs["server"] = config.REMOTE_SERVER
        kwargs["remote_admin"] = remote_reverse("admin:index")
        kwargs["prod_logout"] = local_reverse(admin_urlname(opts, "remote_logout"))
        kwargs["prod_credentials"] = config.get_credentials(request)
        kwargs["prod_login"] = local_reverse(admin_urlname(opts, "remote_login"))
        kwargs["login_url"] = remote_reverse(admin_urlname(opts, "check_login"))

        return super().get_common_context(request, pk, **kwargs)


class CollectMixin(ModelAdmin[Model]):
    sync_collect_related = False
    sync_allow_inspect = True
    protocol_class: type[BaseProtocol] = LoadDumpProtocol

    def check(self) -> list[checks.Error]:
        errors = []
        if not hasattr(self.model, "natural_key"):
            errors.append(
                checks.Warning(
                    f"{self.model} does not use natural_key",
                    hint=f"Add 'natural_keys()` to {self.model} Model."
                    "See https://docs.djangoproject.com/en/4.1/topics/serialization/#natural-keys",
                    obj=self,
                    id="admin-sync.E002",
                )
            )
        return []

    def get_sync_data(self, request: HttpRequest, source: QuerySet[NaturalKeyModel]) -> str:
        return self.protocol_class(request).serialize(source)

    def admin_sync_show_inspect(self) -> bool:
        return self.sync_allow_inspect


class GetManyFromRemoteMixin(CollectMixin, RemoteLogin):
    @button(
        change_list=True,
        change_form=False,
        order=999,
        permission=check_sync_permission,
        visible=is_local,
    )
    def display_remotes(self, request: HttpRequest) -> HttpResponse | HttpResponseRedirect | None:
        if not is_logged_to_remote(request):
            url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
            return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")

        context = self.get_common_context(
            request,
            title="Display REMOTE",
            server=config.REMOTE_SERVER,
            remote_admin=remote_reverse(admin_urlname(self.model._meta, "dumpdata_qs")),
        )
        if request.method == "POST":
            try:
                data = self.get_remote_data(request, "dumpdata_qs")
                return JsonResponse(json.loads(data), safe=False)
            except PermissionError:
                self.message_user(request, "Permission Denied", messages.ERROR)
            except Exception as e:
                logger.exception(e)
                self.message_error_to_user(request, e)
        else:
            return render(request, "admin/admin_sync/get_data.html", context)

    @button(
        change_list=True,
        change_form=False,
        order=999,
        permission=check_sync_permission,
        visible=is_local,
    )
    def get_qs_from_remote(self, request: HttpRequest) -> HttpResponse | HttpResponseRedirect | None:
        if not is_logged_to_remote(request):
            url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
            return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")

        context = self.get_common_context(
            request,
            title="Load data from REMOTE",
            server=config.REMOTE_SERVER,
            remote_admin=remote_reverse(admin_urlname(self.model._meta, "dumpdata_qs")),
        )
        if request.method == "POST":
            try:
                data = self.get_remote_data(request, "dumpdata_qs")
                result = self.protocol_class(request).deserialize(data)
                context["result"] = result
                admin_sync_data_fetched.send(sender=self, data=data)
                self.message_user(request, "Success", messages.SUCCESS)
                return render(request, "admin/admin_sync/get_data_done.html", context)
            except PermissionError:
                url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
                return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")
            except Exception as e:
                logger.exception(e)
                self.message_error_to_user(request, e)
        else:
            return render(request, "admin/admin_sync/get_data.html", context)

    @view(
        decorators=[csrf_exempt],
        http_basic_auth=True,
        enabled=is_remote,
        permission=check_sync_permission,
    )
    def dumpdata_qs(self, request: HttpRequest) -> HttpResponse:
        try:
            data = []
            s = self.get_sync_data(request, self.get_queryset(request))
            data.extend(json.loads(s))
            return SyncResponse(data)
        except Exception as e:
            logger.exception(e)
            self.message_error_to_user(request, e)
            return SyncErrorResponse(str(e).encode("utf-8"))

    def check_sync_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:  # noqa: PLR6301, ARG002
        return request.user.is_staff


class GetSingleFromRemoteMixin(CollectMixin, RemoteLogin):
    @button(label=_("fetch"), visible=is_local, order=999, permission=check_sync_permission)
    def sync(self, request: HttpRequest, pk: str) -> HttpResponseRedirect | HttpResponse | None:
        context = self.get_common_context(request, pk, title="Fetching from REMOTE")
        if request.method == "POST":
            try:
                if not is_logged_to_remote(request):
                    raise PermissionError
                obj = context["original"]
                data = self.get_remote_data(request, "dumpdata_single", obj)
                info = self.protocol_class(request).deserialize(data)
                context["stdout"] = {"details": info}
                admin_sync_data_fetched.send(sender=self, data=data)
                self.message_user(request, "Success", messages.SUCCESS)
                return render(request, "admin/admin_sync/sync_done.html", context)
            except PermissionError:
                url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
                return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")
            except Exception as e:
                logger.exception(e)
                self.message_error_to_user(request, e)
        else:
            if not is_logged_to_remote(request):
                url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
                return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")

            return render(request, "admin/admin_sync/sync.html", context)

    @view(
        decorators=[csrf_exempt],
        http_basic_auth=True,
        enabled=is_remote,
        permission=check_sync_permission,
    )
    def dumpdata_single(self, request: HttpRequest, key: str) -> SyncResponse | HttpResponseRedirect:
        try:
            data = []
            obj = self.model.objects.get_by_natural_key(*key.split("|"))
            s = self.get_sync_data(request, [obj])
            data.extend(json.loads(s))
            return SyncResponse(data)
        except Exception as e:
            logger.exception(e)
            self.message_error_to_user(request, e)
            return HttpResponseRedirect("..")

    def check_sync_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:  # noqa: PLR6301, ARG002
        return request.user.is_staff


def aaa(btn: ButtonWidget) -> bool:
    return True


class PublishMixin(CollectMixin, BaseSyncMixin):
    def get_serializer(self, fmt: str) -> Serializer:  # noqa: PLR6301
        return get_serializer(fmt)()

    def can_publish(self, request: HttpRequest, pk: str | None = None, obj: Model | None = None) -> bool:  # noqa: ARG002 PLR6301
        return True

    def post_data_to_remote(self, request: HttpRequest, data: dict[str, Any]) -> dict[str, str]:
        url = remote_reverse(admin_urlname(self.model._meta, "receive"))
        return self.post_remote_data(request, url, data)

    @button(visible=is_local, order=999, permission=check_publish_permission)
    def publish(self, request: HttpRequest, pk: str) -> HttpResponse | None:
        context = self.get_common_context(request, pk, title="Publish to REMOTE")
        obj = context["original"]
        if not self.can_publish(request, pk, obj):
            return None
        if request.method == "POST":
            try:
                if not is_logged_to_remote(request):
                    raise PermissionError
                data = self.get_sync_data(request, [obj])
                self.post_data_to_remote(request, wraps(data))
                admin_sync_data_published.send(sender=self, data=data)
                self.message_user(request, "Success", messages.SUCCESS)
            except PermissionError:
                url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
                return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")
            except PublishError as e:
                logger.exception(e)
                self.message_error_to_user(request, f"{e}")
            except Exception as e:
                logger.exception(e)
                self.message_error_to_user(request, e)
        elif not is_logged_to_remote(request):
            url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
            return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")
        return render(request, "admin/admin_sync/publish.html", context)

    @view(decorators=[csrf_exempt], http_basic_auth=True)
    def receive(self, request: HttpRequest) -> HttpResponse:
        try:
            raw_data = unwrap(request.body.decode())
            data = self.protocol_class(request).deserialize(raw_data)
            admin_sync_data_received.send(sender=self, data=data)
            return JsonResponse(
                {
                    "message": "Done",
                    "details": data,
                },
                status=200,
            )
        except Exception as e:  # noqa: BLE001
            return JsonResponse(
                {
                    "error": str(e),
                },
                status=HTTPStatus.BAD_REQUEST,
            )

    @view(decorators=[csrf_exempt], http_basic_auth=True)
    def done(self, request: HttpRequest, pk: str, tpl: str) -> HttpResponse:
        context = self.get_common_context(request, pk, title="Publish to REMOTE")
        return render(request, f"admin/admin_sync/{tpl}.html", context)

    def check_publish_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:  # noqa: ARG002, PLR6301
        return request.user.is_staff

    @button(
        visible=lambda b: b.handler.model_admin.admin_sync_show_inspect(),
        html_attrs={"style": "background-color:red"},
    )
    def admin_sync_inspect_single(self, request: HttpRequest, pk: str) -> HttpResponse:
        context = self.get_common_context(request, pk, title="Sync Inspect")
        collector = self.protocol_class(request)
        data = collector.collect([self.get_object(request, pk)])
        context["data"] = data
        return render(request, "admin/admin_sync/inspect.html", context)


class SyncMixin(GetManyFromRemoteMixin, GetSingleFromRemoteMixin, PublishMixin):
    pass


class SyncModelAdmin(SyncMixin, admin.ModelAdmin):
    pass
