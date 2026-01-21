from json import dumps as json_dumps
from os import environ
from tempfile import NamedTemporaryFile

import pytest


def __tmp_json_file() -> str:
    """Creates a temporary JSON file and returns it's path."""
    with NamedTemporaryFile("w", delete=False) as repos:
        repos.write(json_dumps({}))
        return repos.name


@pytest.fixture
def app(requests_mock):
    """Returns a mocked app with TESTING=True, no CRSF and mocked forms"""

    # Mock forms
    forms_url: str = "http://totally.forms"
    environ["FORMS_URL"] = forms_url
    requests_mock.post(forms_url)

    environ["FORMS_FILE"] = __tmp_json_file()

    from reuse_api import create_app  # noqa: PLC0415

    app = create_app()

    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    yield app

    app.scheduler.join()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
