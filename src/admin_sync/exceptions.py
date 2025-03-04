from requests import Response


class VersionMismatchError(Exception):
    pass


class RemoteError(Exception):
    pass


class SyncError(Exception):
    pass


class PublishError(Exception):
    def __init__(self, response: Response) -> None:
        self.response = response

    def __str__(self) -> str:
        return self.response.json()["error"]


class ProtocolError(Exception):
    def __init__(self, cause: Exception) -> None:
        self.cause = cause

    def __str__(self) -> str:
        if self.cause.__cause__ and hasattr(self.cause, "obj"):
            return f"{self.cause.obj.__class__.__name__}: {self.cause.obj}: {self.cause}"
        return f"{self.__class__.__name__}: {self.cause}"


class UnsupportedError(Exception):
    message = "Remote server does not seem to be a Admin-Sync enabled site."
