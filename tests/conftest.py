# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later


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
def client(_mock_forms_url, mocked_forms_app):
    """A test client for the app."""
    yield mocked_forms_app.test_client()
    mocked_forms_app.scheduler.join()


@pytest.fixture
def _mock_forms_url(requests_mock):
    url = "http://test-url.fsfe"
    environ["FORMS_URL"] = url

    requests_mock.post(url)


@pytest.fixture
def mocked_forms_app():

    environ["FORMS_FILE"] = __tmp_json_file()

    from reuse_api import create_app  # noqa: PLC0415

    app = create_app()

    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    return app
