# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from http import HTTPStatus


FSFE_URL: str = "fsfe.org/reuse/api"


def gendata(url: str, email: str = "my_email@fsfe.org", name="some_name") -> dict:
    """Generates POST data contents for testing."""
    return {"project": url, "confirm": email, "name": name}


def test_root_url(client):
    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    assert "REUSE" in response.data.decode()


def test_register(client):
    response = client.post("/register", data=gendata("git." + FSFE_URL))

    assert response.status_code == HTTPStatus.ACCEPTED


def test_register_double_with_protocol(client):
    response = client.post("/register", data=gendata("https://git." + FSFE_URL))

    assert response.status_code == HTTPStatus.ACCEPTED


def test_register_failed_not_a_git_repository(client):
    response = client.post("/register", data=gendata(FSFE_URL))

    assert response.status_code == HTTPStatus.OK
    assert "Not a Git repository" in response.data.decode()


def test_register_failed_due_to_schema(client):
    response = client.post("/register", data=gendata("git.fsfe.org:reuse/api"))

    assert response.status_code == HTTPStatus.OK
    assert "Not a Git repository" in response.data.decode()
