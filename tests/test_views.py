# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later


def test_root_url(client):
    r = client.get("/")

    assert r.status_code == 200
    assert "REUSE" in r.data.decode()


def test_register(client):
    data = {
        "name": "my_project",
        "confirm": "my_email@fsfe.org",
        "project": "git.fsfe.org/reuse/api",
    }
    r = client.post("/register", data=data)

    assert r.status_code == 200
    assert "Registration successful" in r.data.decode()


def test_register_failed_due_to_schema(client):
    data = {
        "name": "my_project",
        "confirm": "my_email@fsfe.org",
        "project": "https://fsfe.org/reuse/api",
        "wantupdates": True,
    }
    r = client.post("/register", data=data)

    assert r.status_code == 200
    assert "Not a Git repository" in r.data.decode()


def test_register_failed_not_a_git_repository(client):
    data = {
        "name": "my_project",
        "confirm": "my_email@fsfe.org",
        "project": "git.fsfe.org:reuse/api",
        "wantupdates": True,
    }
    r = client.post("/register", data=data)

    assert r.status_code == 200
    assert "Not a Git repository" in r.data.decode()
