class VersionMismatchError(Exception):
    pass


class RemoteError(Exception):
    pass


class SyncError(Exception):
    pass


class ProtocolError(Exception):
    def __init__(self, cause: Exception) -> None:
        self.cause = cause

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.cause}"


class UnsupportedError(Exception):
    message = "Remote server does not seem to be a Admin-Sync enabled site."
