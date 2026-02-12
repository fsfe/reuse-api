from typing import Any, cast, override

from flask import Flask, current_app

from reuse_api.manager import Manager, manager


class ReuseApp(Flask):

    @override
    def __init__(self, import_name: str, **kwargs: Any) -> None:
        """Flask override with Manager added."""
        super().__init__(import_name, **kwargs)
        self.__mgr: Manager = manager

    def handle(self, repo: str, min_age: int = 15) -> None:
        """Wrapper for Manager's handle."""
        self.__mgr.handle(repo, min_age)

    def cleanup(self) -> None:
        """Wrapper for Manager's cleanup."""
        self.__mgr.cleanup()


# Typed wrapper for Flask.current_app
reuse_app: ReuseApp = cast("ReuseApp", current_app)
