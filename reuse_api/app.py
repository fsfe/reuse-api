"""ReuseAPP class that inherits from Flask & typed current_app wrapper."""

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, cast, override

from flask import Flask, current_app

from reuse_api.db import is_older_than, update


class ReuseApp(Flask):
    """ReuseApp is Flask with an executor.

    It's purpose os to provide a clean and idiomatic way of
    scheduling tasks with logging and additional logic.
    """

    @override
    def __init__(self, import_name: str, **kwargs: Any) -> None:
        """Flask override with an Executor added."""
        super().__init__(import_name, **kwargs)
        self.__executor: ThreadPoolExecutor = ThreadPoolExecutor()

    def _update(self, repo: str) -> None:
        """Async wrapper for db.update with logging."""
        self.logger.info("Task submitted: %s", repo)
        future: Future = self.__executor.submit(update, repo)

        _ = future.result()  # Print after job is done
        self.logger.info("Task finished %s", repo)

    def handle(self, repo: str, min_age: int = 15) -> None:
        """Handle the database update with additional logic.

        Created for putting it in view functions.
        """
        if not is_older_than(repo, min_age):
            return
        # potentially more conditions

        self._update(repo)

    def cleanup(self) -> None:  # pragma: no cover
        """Shutdown the internal executor."""
        self.__executor.shutdown()


# Typed wrapper for Flask.current_app
reuse_app: ReuseApp = cast("ReuseApp", current_app)
