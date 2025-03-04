from typing import TypeAlias

from django.db.models import Model, QuerySet

Collectable: TypeAlias = QuerySet[Model] | list[Model]
