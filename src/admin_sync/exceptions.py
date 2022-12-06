from django.core.serializers.base import DeserializedObject


class VersionMismatchError(Exception):
    pass


class PublishError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return self.response.json()["error"]


class ProtocolError(Exception):
    def __init__(self, cause: Exception):
        self.cause = cause.__cause__

    def __str__(self):
        return f"{self.cause.obj.__class__.__name__}: {self.cause.obj}: {self.cause}"
