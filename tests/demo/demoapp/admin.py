import os
from typing import Iterable

from admin_extra_buttons.decorators import button
from django.contrib.admin import site
from django.contrib.auth.admin import UserAdmin
from django.db.models import Model
from django.http import HttpRequest, HttpResponse
from reversion.admin import VersionAdmin

from admin_sync.mixin import SyncMixin, SyncModelAdmin
from admin_sync.protocol import BaseProtocol, LoadDumpProtocol

from .models import Base, Detail, Tag


class SyncUserAdmin(SyncMixin, UserAdmin):
    pass


class BaseModelAdmin(SyncMixin):
    pass


class DetailProtocol(LoadDumpProtocol):
    def collect(self, data) -> Iterable[Model]:
        parents = []
        c = self.collector_class(collect_related=True)
        c.collect(data)
        for o in c.data:
            if isinstance(o, Detail) and o.brother:
                parents.append(o.brother)
        return parents


class DetailModelAdmin(SyncMixin, VersionAdmin):
    protocol_class = DetailProtocol


site.register(Base, BaseModelAdmin)
site.register(Detail, DetailModelAdmin)
site.register(Tag, SyncModelAdmin)

if os.environ.get("ADMIN_SYNC_REMOTE"):
    site.site_header = "AdminSync REMOTE"
    site.site_title = "AdminSync REMOTE"
    site.index_title = "AdminSync REMOTE"
else:
    site.site_header = "AdminSync LOCAL"
    site.site_title = "AdminSync LOCAL"
    site.index_title = "AdminSync LOCAL"
