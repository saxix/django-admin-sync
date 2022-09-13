from reversion.admin import VersionAdmin

from django.contrib.admin import site
from django.contrib.auth.admin import UserAdmin

from admin_sync.mixin import SyncMixin, SyncModelAdmin

from .models import Base, Detail, Tag


class SyncUserAdmin(SyncMixin, UserAdmin):
    pass


class BaseModelAdmin(VersionAdmin, SyncMixin):
    pass


site.register(Base, BaseModelAdmin)
site.register(Detail, SyncModelAdmin)
site.register(Tag, SyncModelAdmin)
