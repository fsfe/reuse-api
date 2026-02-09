# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Flask application factory."""

import logging
from atexit import register as atexit_register
from os import R_OK, access, environ, makedirs, path
from os.path import isfile

from flask import Flask

from reuse_api.views import HTML, JSON


def __formsfile_checks(forms_file: str) -> None:
    """Makes sure that FORMS_FILE is there and readable."""
    if isfile(forms_file):
        if not access(forms_file, R_OK):  # pragma: no cover
            raise PermissionError(
                "FORMS_FILE is not readable:",
                path.abspath(forms_file),
            )
    else:
        with open(forms_file, "w") as f:
            f.write("[]")


def create_app() -> Flask:
    # Disable git prompt
    environ["GIT_TERMINAL_PROMPT"] = "0"

    # Configure logging format
    logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s")

    # Create and configure the app
    app: Flask = Flask(__name__.split(".")[0])
    app.config.from_object(config)
    app.logger.setLevel(logging.DEBUG)
    # Perform sanity checks
    __formsfile_checks(str(app.config.get("FORMS_FILE")))

    app.register_blueprint(HTML)
    app.register_blueprint(JSON)

    app.logger.debug("Running config: %s", app.config)

    # Initialize database
    makedirs(str(app.config.get("REUSE_DB_PATH")), exist_ok=True)

    return app
