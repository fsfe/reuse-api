# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

PROJECT: str = "my_project"
EMAIL: str = "my_email@fsfe.org"
FSFE_URL: str = "fsfe.org/reuse/api"


def test_root_url(client):
    r = client.get("/")

    assert r.status_code == 200
    assert "REUSE" in r.data.decode()


def test_register(client):
    data = {
        "name": PROJECT,
        "confirm": EMAIL,
        "project": "git." + FSFE_URL,
    }
    r = client.post("/register", data=data)

    assert r.status_code == 200
    assert "Registration successful" in r.data.decode()


def test_register_double_with_protocol(client):
    data = {
        "name": PROJECT,
        "confirm": EMAIL,
        "project": "https://git." + FSFE_URL,
    }
    r = client.post("/register", data=data)

    assert r.status_code == 200
    assert "Registration successful" in r.data.decode()


def test_register_failed_not_a_git_repository(client):
    data = {
        "name": PROJECT,
        "confirm": EMAIL,
        "project": FSFE_URL,
        "wantupdates": True,
    }
    r = client.post("/register", data=data)

    assert r.status_code == 200
    assert "Not a Git repository" in r.data.decode()


def test_register_failed_due_to_schema(client):
    data = {
        "name": PROJECT,
        "confirm": EMAIL,
        "project": "git.fsfe.org:reuse/api",
        "wantupdates": True,
    }
    r = client.post("/register", data=data)

    assert r.status_code == 200
    assert "Not a Git repository" in r.data.decode()
