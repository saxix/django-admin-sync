from __future__ import annotations

from typing import Iterable

from django.db.models import Model, QuerySet

type Collectable = QuerySet[Model] | Iterable[Model]

class SyncResponse[TypedDict]:
    message: str

class NaturalKeyModel(Model):
    def natural_key(self) -> tuple[str, ...]: ...
