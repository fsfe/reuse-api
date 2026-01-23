from os import environ

import pytest


@pytest.fixture
def tmp_json(tmp_path) -> str:
    """Creates a temporary JSON file and returns it's path."""
    tmpfile = tmp_path / "repos.json"
    tmpfile.write_text("[]")
    return str(tmpfile)


@pytest.fixture
def app(requests_mock, tmp_json):
    """Returns a mocked app with TESTING=True, no CRSF and mocked forms"""
    environ["FORMS_FILE"] = tmp_json

    # Mock forms
    forms_url: str = "http://totally.forms"
    environ["FORMS_URL"] = forms_url
    requests_mock.post(forms_url)

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
