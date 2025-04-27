import contextlib
from collections.abc import Generator

try:
    from reversion import (
        create_revision as reversion_create_revision,
    )
    from reversion import (
        set_comment as reversion_set_comment,
    )
    from reversion import (
        set_user as reversion_set_user,
    )
except ImportError:
    reversion_set_user = reversion_set_comment = lambda *k: True  # noqa: ARG005

    @contextlib.contextmanager
    def reversion_create_revision() -> Generator[None]:
        yield


try:
    from concurrency.api import disable_concurrency
except ImportError:

    @contextlib.contextmanager
    def disable_concurrency() -> Generator[None]:
        yield
