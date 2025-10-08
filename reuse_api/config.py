# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Configuration for the REUSE API service"""

import os


# Configuration for Flask
SECRET_KEY: str = os.environ.get("SECRET_KEY", "secret_key")

# Admin key for the REUSE API, necessary for some operations
ADMIN_KEY: str = os.environ.get("ADMIN_KEY", "admin_key")

# Configuration for the repository storage
# NOTE: A relative path currently (Flask-SQLAlchemy < 3.0) is relative to the
# application root, not relative to the current working directory! So we have
# to define an absolute path.
# See also https://github.com/pallets/flask-sqlalchemy/issues/462
SQLALCHEMY_DATABASE_URI: str = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
)
SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

# Configuration for the form server used for registration
FORMS_URL: str = os.environ.get("FORMS_URL", "https://forms.fsfe.org/email")
FORMS_FILE: str = os.environ.get("FORMS_FILE", "repos.json")
if not os.path.isfile(FORMS_FILE):
    raise FileNotFoundError(
        "Can't run without access to the '%s' file", FORMS_FILE
    )

# SSH configurations
SSH_KEY_PATH: str = os.environ.get("SSH_KEY_PATH", "~/.ssh/reuse_ed25519")
SSH_KNOW_HOST_PATH: str = os.environ.get(
    "SSH_KNOW_HOST_PATH", "~/.ssh/known_hosts"
)
SSH_PORT: int = int(os.environ.get("SSH_PORT", "22"))
SSH_USER: str = os.environ.get("SSH_USER", "reuse")

# Servername
REUSE_API: str = os.environ.get("REUSE_API", "wrk1.api.reuse.software")

# Number of maximum checks in queue
NB_RUNNER: int = int(os.environ.get("NB_RUNNER", "6"))

# Number of repository return during pagination
NB_REPOSITORY_BY_PAGINATION: int = int(
    os.environ.get("NB_REPOSITORY_BY_PAGES", "10")
)
