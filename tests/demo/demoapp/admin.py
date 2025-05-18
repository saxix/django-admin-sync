import os
from typing import Iterable

from django.contrib.admin import site
from django.contrib.auth.admin import UserAdmin
from django.db.models import Model

from admin_sync.mixins import SyncModelAdmin, SyncPushMixin
from admin_sync.protocol import LoadDumpProtocol

from .models import Base, Detail, Tag, MissingNaturalKey


class SyncUserAdmin(SyncModelAdmin, UserAdmin):
    def admin_sync_show_inspect(self) -> bool:
        return True


class BaseModelAdmin(SyncPushMixin):
    pass


class DetailProtocol(LoadDumpProtocol):
    def collect(self, data) -> Iterable[Model]:
        c = self.collector_class(collect_related=True)
        c.collect(data)
        return [o.brother for o in c.data if isinstance(o, Detail) and o.brother]


class DetailModelAdmin(SyncPushMixin):
    protocol_class = DetailProtocol


site.register(Base, BaseModelAdmin)
site.register(Detail, DetailModelAdmin)
site.register(Tag, SyncModelAdmin)
site.register(MissingNaturalKey, SyncModelAdmin)

if os.environ.get("ADMIN_SYNC_REMOTE"):
    site.site_header = "AdminSync REMOTE"
    site.site_title = "AdminSync REMOTE"
    site.index_title = "AdminSync REMOTE"
else:
    site.site_header = "AdminSync LOCAL"
    site.site_title = "AdminSync LOCAL"
    site.index_title = "AdminSync LOCAL"
