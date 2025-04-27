from django.db.models import Model, QuerySet

type Collectable = QuerySet[Model] | list[Model]
