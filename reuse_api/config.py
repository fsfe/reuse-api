# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Configuration for the REUSE API service"""

from os import getenv, path


# Configuration for Flask
SECRET_KEY: str = getenv("SECRET_KEY", default="secret_key")

# Admin key for the REUSE API, necessary for some operations
ADMIN_KEY: str = getenv("ADMIN_KEY", default="admin_key")

# Configuration for the repository storage
# NOTE: A relative path currently (Flask-SQLAlchemy < 3.0) is relative to the
# application root, not relative to the current working directory! So we have
# to define an absolute path.
# See also https://github.com/pallets/flask-sqlalchemy/issues/462
SQLALCHEMY_DATABASE_URI: str = getenv(
    "SQLALCHEMY_DATABASE_URI", default="sqlite:///:memory:"
)
SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

# Configuration for the form server used for registration
FORMS_URL: str = getenv("FORMS_URL", default="https://forms.fsfe.org/email")
FORMS_FILE: str = getenv("FORMS_FILE", default="repos.json")
if not path.isfile(FORMS_FILE):
    raise FileNotFoundError(
        "Can't run without access to the '%s' file", FORMS_FILE
    )

# SSH configurations
SSH_KEY_PATH: str = getenv("SSH_KEY_PATH", default="~/.ssh/reuse_ed25519")
SSH_KNOW_HOST_PATH: str = getenv(
    "SSH_KNOW_HOST_PATH", default="~/.ssh/known_hosts"
)
SSH_PORT: int = int(getenv("SSH_PORT", default=22))
SSH_USER: str = getenv("SSH_USER", "reuse")

# Servername
REUSE_API: str = getenv("REUSE_API", "wrk1.api.reuse.software")

# Number of maximum checks in queue
NB_RUNNER: int = int(getenv("NB_RUNNER", default=6))

# Number of repository return during pagination
NB_REPOSITORY_BY_PAGINATION: int = int(
    getenv("NB_REPOSITORY_BY_PAGES", default=10)
)
