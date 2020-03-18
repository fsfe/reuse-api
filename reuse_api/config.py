# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Configuration for the REUSE API service"""

import os


# Configuration for Flask
SECRET_KEY = os.environ.get("SECRET_KEY", "secret_key")
SEND_FILE_MAX_AGE_DEFAULT = 60

# Configuration for the repository storage
# NOTE: A relative path currently (Flask-SQLAlchemy < 3.0) is relative to the
# application root, not relative to the current working directory! So we have
# to define an absolute path.
# See also https://github.com/pallets/flask-sqlalchemy/issues/462
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.getcwd()}/database.sqlite"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configuration for the form server used for registration
FORMS_URL = "https://forms.fsfe.org/email"
FORMS_FILE = "repos.json"

# TODO: SERVERNAME
