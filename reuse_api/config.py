# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Configuration for the REUSE API service"""

import os


# Configuration for Flask
SECRET_KEY = os.environ.get("SECRET_KEY", "secret_key")

# Configuration for the repository storage
# NOTE: A relative path currently (Flask-SQLAlchemy < 3.0) is relative to the
# application root, not relative to the current working directory! So we have
# to define an absolute path.
# See also https://github.com/pallets/flask-sqlalchemy/issues/462
SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configuration for the form server used for registration
FORMS_URL = os.environ.get("FORMS_URL", "https://forms.fsfe.org/email")
FORMS_FILE = os.environ.get("FORMS_FILE", "repos.json")
if not os.path.isfile(FORMS_FILE):
    raise FileNotFoundError(
        "Can't run without access to the '%s' file", FORMS_FILE
    )

# SSH configurations
SSH_KEY_PATH = os.environ.get("SSH_KEY_PATH", "~/.ssh/reuse_ed25519")
SSH_KNOW_HOST_PATH = os.environ.get("SSH_KNOW_HOST_PATH", "~/.ssh/known_hosts")
SSH_USER = os.environ.get("SSH_USER", "reuse")

# Servername
REUSE_API = os.environ.get("REUSE_API", "wrk3.api.reuse.software")

# Number of maximum checks in queue
NB_RUNNER = int(os.environ.get("NB_RUNNER", "6"))

# Number of repository return during pagination
NB_REPOSITORY_BY_PAGINATION = int(
    os.environ.get("NB_REPOSITORY_BY_PAGES", "10")
)
