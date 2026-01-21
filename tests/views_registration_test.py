# SPDX-FileCopyrightText: 2025 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from http import HTTPStatus


from reuse_api.db import is_registered, register

from .conftest import TEST_REPO


def gendata(url: str, email: str = "my_email@fsfe.org", name="some_name") -> dict:
    """Generates POST data contents for testing."""
    return {"project": url, "confirm": email, "name": name}


def test_registration_empty_post(client) -> None:
    response = client.post("/register", data={})
    assert response.status_code == HTTPStatus.OK


def test_registration_without_forms(app, client, db_empty) -> None:
    app.config["FORMS_DISABLE"] = True
    response = client.post("/register", data=gendata(TEST_REPO))
    assert response.status_code == HTTPStatus.ACCEPTED
    assert is_registered(TEST_REPO)


def test_registration_mocked_forms(app, client, db_empty) -> None:
    app.config["FORMS_DISABLE"] = False
    response = client.post("/register", data=gendata(TEST_REPO))
    assert response.status_code == HTTPStatus.ACCEPTED
    assert not is_registered(TEST_REPO)
