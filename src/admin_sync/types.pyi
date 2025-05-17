from django.db.models import Model, QuerySet

type Collectable = QuerySet[Model] | list[Model]

class SyncResponse[TypedDict]:
    message: str
