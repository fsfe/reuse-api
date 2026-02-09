"""
This file contains the definition of the Manager class and it's instance.

Only the singleton should be used externally.
"""

from concurrent.futures import Future, ThreadPoolExecutor

from flask import current_app

from reuse_api.db import is_older_than, update


class Manager:
    """Singleton class that wraps PoolExecutor with logging."""

    __executor: ThreadPoolExecutor = ThreadPoolExecutor()

    def cleanup(self) -> None:  # pragma: no cover
        """Wrapper for the executor shutdown"""
        self.__executor.shutdown()

    def _update(self, url: str) -> None:
        """Async wrapper for db.update with logging."""
        current_app.logger.info("Task submitted: %s", url)
        future: Future = self.__executor.submit(update, url)

        _ = future.result()  # Print after job is done
        current_app.logger.info("Task finished %s", url)

    def handle(self, repo: str, min_age: int = 15) -> None:
        """Handles the database update with additional logic.
        Created for putting it in view functions"""
        if not is_older_than(repo, min_age):
            return

        self._update(repo)


manager: Manager = Manager()
