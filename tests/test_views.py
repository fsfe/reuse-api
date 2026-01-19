# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from http import HTTPStatus


PROJECT: str = "my_project"
EMAIL: str = "my_email@fsfe.org"
FSFE_URL: str = "fsfe.org/reuse/api"


def test_root_url(client):
    response = client.get("/")

    assert response.status_code == HTTPStatus.OK
    assert "REUSE" in response.data.decode()


def test_register(client):
    data = {
        "name": PROJECT,
        "confirm": EMAIL,
        "project": "git." + FSFE_URL,
    }
    response = client.post("/register", data=data)

    assert response.status_code == HTTPStatus.ACCEPTED
    assert "Registration successful" in response.data.decode()


def test_register_double_with_protocol(client):
    data = {
        "name": PROJECT,
        "confirm": EMAIL,
        "project": "https://git." + FSFE_URL,
    }
    response = client.post("/register", data=data)

    assert response.status_code == HTTPStatus.ACCEPTED
    assert "Registration successful" in response.data.decode()


def test_register_failed_not_a_git_repository(client):
    data = {
        "name": PROJECT,
        "confirm": EMAIL,
        "project": FSFE_URL,
        "wantupdates": True,
    }
    response = client.post("/register", data=data)

    assert response.status_code == HTTPStatus.OK
    assert "Not a Git repository" in response.data.decode()


def test_register_failed_due_to_schema(client):
    data = {
        "name": PROJECT,
        "confirm": EMAIL,
        "project": "git.fsfe.org:reuse/api",
        "wantupdates": True,
    }
    response = client.post("/register", data=data)

    assert response.status_code == HTTPStatus.OK
    assert "Not a Git repository" in response.data.decode()
