from os import environ

import pytest

from reuse_api import create_app

environ["GIT_TERMINAL_PROMPT"] = "0"
TEST_REPO: str = "git.fsfe.org/reuse/api"


@pytest.fixture
def tmp_json(tmp_path) -> str:
    """Creates a temporary JSON file and returns it's path."""
    tmpfile = tmp_path / "repos.json"
    tmpfile.write_text("[]")
    return str(tmpfile)


@pytest.fixture
def app(tmp_json):
    """Returns a mocked app with TESTING=True, no CRSF and mocked forms"""
    environ["FORMS_FILE"] = tmp_json

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    yield app

    app.scheduler.join()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


# Database fixtures
from reuse_api import db


@pytest.fixture
def db_empty() -> None:
    db.drop(really=True)


@pytest.fixture
def db_registered(db_empty) -> None:
    db.register(TEST_REPO)


@pytest.fixture
def db_updated(db_registered) -> None:
    db.update(TEST_REPO)
