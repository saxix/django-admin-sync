import io
import json
import logging
import requests
from json import JSONDecodeError
from requests.auth import HTTPBasicAuth
from urllib.parse import quote_plus, unquote_plus

from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core import checks, signing
from django.core.serializers import get_serializer
from django.core.validators import ValidationError
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls.base import reverse as local_reverse
from django.views.decorators.csrf import csrf_exempt

from admin_extra_buttons.api import ExtraButtonsMixin, button, view

from .conf import PROTOCOL_VERSION, config
from .exceptions import PublishError, VersionMismatchError
from .forms import ProductionLoginForm
from .perms import check_publish_permission, check_sync_permission
from .protocol import BaseProtocol, LoadDumpProtocol
from .signals import (
    admin_sync_data_fetched,
    admin_sync_data_published,
    admin_sync_data_received,
)
from .utils import (
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

logger = logging.getLogger(__name__)

signer = signing.TimestampSigner()


class BaseSyncMixin(ExtraButtonsMixin):
    def post_remote_data(self, request, url, data):
        auth = None
        if credentials := config.get_credentials(request):
            auth = HTTPBasicAuth(**credentials)
        ret = requests.post(url, data=data, auth=auth)
        if ret.status_code == 400:
            raise PublishError(ret)
        if ret.status_code == 403:
            raise PermissionError
        if ret.status_code == 404:
            raise Http404(url)
        return ret.json()

    def get_remote_data(self, request, urlname, obj=None):
        if obj:
            natural_key = "|".join(obj.natural_key())
            url = remote_reverse(
                admin_urlname(self.model._meta, urlname), args=[natural_key]
            )
        else:
            url = remote_reverse(admin_urlname(self.model._meta, urlname))

        auth = None
        if credentials := config.get_credentials(request):
            auth = HTTPBasicAuth(**credentials)
        ret = requests.get(url, auth=auth)
        if ret.status_code == 403:
            raise PermissionError
        if ret.status_code == 404:
            raise Http404(config.REMOTE_SERVER + url)
        try:
            if (
                config.RESPONSE_HEADER
                and ret.headers[config.RESPONSE_HEADER] != PROTOCOL_VERSION
            ):
                raise VersionMismatchError(
                    "Remote site is using an incompatible protocol."
                )
            payload = unwrap(ret.content)
        except JSONDecodeError as e:
            logger.exception(e)
            raise Exception("%s: %s" % (ret.status_code, ret.content))
        except KeyError:
            raise Exception(
                "Remote server does not seem to be a Admin-Sync enabled site."
            )
        except Exception as e:
            logger.exception(e)
            raise
        return payload


class RemoteLogin(BaseSyncMixin):
    @view(decorators=[csrf_exempt], http_basic_auth=True, enabled=is_remote)
    def check_login(self, request):
        response = JsonResponse({"user": request.user.username})
        set_cookie(response, "editor_logged", "1")
        return response

    @view(decorators=[csrf_exempt], http_basic_auth=True, enabled=is_remote)
    def remote_logout(self, request):
        redir_url = request.build_absolute_uri(
            unquote_plus(request.GET.get("from", ".."))
        )
        response = HttpResponseRedirect(redir_url)
        response.delete_cookie(config.CREDENTIALS_COOKIE)
        return response

    @view(enabled=is_local)
    def remote_login(self, request):
        context = self.get_common_context(
            request, title=f"Login to remote ({config.REMOTE_SERVER})"
        )
        cookies = {}
        if request.method == "POST":
            form = ProductionLoginForm(data=request.POST)
            if form.is_valid():
                try:
                    basic = HTTPBasicAuth(**form.cleaned_data)
                    url = remote_reverse(admin_urlname(self.model._meta, "check_login"))
                    ret = requests.post(url, auth=basic)
                    if ret.status_code == 200:
                        data = ret.json()
                        if data["user"] != form.cleaned_data["username"]:
                            raise ValidationError("---")
                        cookies[config.CREDENTIALS_COOKIE] = sign_prod_credentials(
                            **form.cleaned_data
                        )
                        data = ret.json()
                        self.message_user(
                            request,
                            f"Logged in to {config.REMOTE_SERVER} as {data['user']}",
                        )
                        if "from" in request.GET:
                            redir_url = request.build_absolute_uri(
                                unquote_plus(request.GET["from"])
                            )
                            response = HttpResponseRedirect(redir_url)
                            response.set_cookie(
                                config.CREDENTIALS_COOKIE,
                                cookies[config.CREDENTIALS_COOKIE],
                            )
                            return response
                    else:
                        self.message_user(
                            request, f"Login failed {ret} - {url}", messages.ERROR
                        )
                except Exception as e:
                    logger.exception(e)
                    self.message_error_to_user(request, e)
        else:
            form = ProductionLoginForm()
        context["form"] = form
        return render(
            request, "admin/admin_sync/login_prod.html", context, cookies=cookies
        )

    def get_common_context(self, request, pk=None, **kwargs):
        kwargs["server"] = config.REMOTE_SERVER
        kwargs["remote_admin"] = remote_reverse("admin:index")
        kwargs["prod_logout"] = local_reverse(
            admin_urlname(self.model._meta, "remote_logout")
        )
        kwargs["prod_credentials"] = config.get_credentials(request)
        kwargs["prod_login"] = local_reverse(
            admin_urlname(self.model._meta, "remote_login")
        )
        kwargs["login_url"] = remote_reverse(
            admin_urlname(self.model._meta, "check_login")
        )

        return super().get_common_context(request, pk, **kwargs)


class CollectMixin:
    sync_collect_related = False
    protocol_class: BaseProtocol = LoadDumpProtocol

    def check(self):
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

    def get_sync_data(self, request, source) -> str:
        return self.protocol_class(request).serialize(source)
        # return collect_data(source, self.sync_collect_related)

    def admin_sync_show_inspect(self):
        return False


class GetManyFromRemoteMixin(CollectMixin, RemoteLogin):
    @button(
        change_list=True,
        change_form=False,
        order=999,
        permission=check_sync_permission,
        visible=is_local,
    )
    def get_qs_from_remote(self, request):
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
    def dumpdata_qs(self, request):
        try:
            data = []
            s = self.get_sync_data(request, self.get_queryset(request))
            data.extend(json.loads(s))
            return SyncResponse(data)
        except Exception as e:
            logger.exception(e)
            self.message_error_to_user(request, e)
            return HttpResponseRedirect("..")

    def check_sync_permission(self, request, obj=None):
        return request.user.is_staff


class GetSingleFromRemoteMixin(CollectMixin, RemoteLogin):
    @button(visible=is_local, order=999, permission=check_sync_permission)
    def sync(self, request, pk):
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
    def dumpdata_single(self, request, key):
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

    def check_sync_permission(self, request, obj=None):
        return request.user.is_staff


class PublishMixin(CollectMixin, BaseSyncMixin):
    def get_serializer(self, fmt):
        return get_serializer(fmt)()

    def post_data_to_remote(self, request, data):
        url = remote_reverse(admin_urlname(self.model._meta, "receive"))
        return self.post_remote_data(request, url, data)

    @button(visible=is_local, order=999, permission=check_publish_permission)
    def publish(self, request, pk):
        context = self.get_common_context(request, pk, title="Publish to REMOTE")
        if request.method == "POST":
            try:
                if not is_logged_to_remote(request):
                    raise PermissionError
                data = self.get_sync_data(request, [self.get_object(request, pk)])
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
        else:
            if not is_logged_to_remote(request):
                url = local_reverse(admin_urlname(self.model._meta, "remote_login"))
                return HttpResponseRedirect(f"{url}?from={quote_plus(request.path)}")
        return render(request, "admin/admin_sync/publish.html", context)

    @view(decorators=[csrf_exempt], http_basic_auth=True)
    def receive(self, request):
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
        except Exception as e:
            # logger.exception(e)
            return JsonResponse(
                {
                    "error": str(e),
                },
                status=400,
            )

    @view(decorators=[csrf_exempt], http_basic_auth=True)
    def done(self, request, pk, tpl):
        context = self.get_common_context(request, pk, title="Publish to REMOTE")
        return render(request, f"admin/admin_sync/{tpl}.html", context)

    def check_publish_permission(self, request, obj=None):
        return request.user.is_staff

    @button(
        # visible=lambda b: b.model_admin.admin_sync_show_inspect(),
        html_attrs={"style": "background-color:red"},
    )
    def admin_sync_inspect(self, request, pk):
        context = self.get_common_context(request, title="Sync Inspect")
        collector = self.protocol_class(request)
        data = collector.collect([self.get_object(request, pk)])
        context["data"] = data
        return render(request, "admin/admin_sync/inspect.html", context)
        # return JsonResponse(c.models, safe=False)


class SyncMixin(GetManyFromRemoteMixin, GetSingleFromRemoteMixin, PublishMixin):
    pass


class SyncModelAdmin(SyncMixin, admin.ModelAdmin):
    pass
