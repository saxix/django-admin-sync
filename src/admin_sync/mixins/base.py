from __future__ import annotations

from admin_extra_buttons.mixins import ExtraButtonsMixin

from admin_sync.protocol import BaseProtocol, LoadDumpProtocol


class BaseSyncMixin(ExtraButtonsMixin):
    protocol_class: type[BaseProtocol] = LoadDumpProtocol
