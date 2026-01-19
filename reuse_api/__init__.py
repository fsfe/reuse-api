# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Flask application factory."""

import logging
from atexit import register as atexit_register
from os import R_OK, access, environ, makedirs, path

from flask import Flask

from reuse_api import config
from reuse_api.views import HTML, JSON

from .scheduler import Scheduler


def create_app() -> Flask:
    # Disable git prompt
    environ["GIT_TERMINAL_PROMPT"] = "0"

    # Configure logging format
    logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s")

    # Perform sanity checks
    if not access(config.FORMS_FILE, R_OK):  # pragma: no cover
        raise PermissionError(
            "FORMS_FILE is not readable:", path.abspath(config.FORMS_FILE)
        )

    # Create and configure the app
    app: Flask = Flask(__name__.split(".")[0])
    app.config.from_object(config)
    app.logger.setLevel(logging.DEBUG)

    app.register_blueprint(HTML)
    app.register_blueprint(JSON)

    app.logger.debug("Running config: %s", app.config)

    # Initialize database
    makedirs(config.REUSE_DB_PATH, exist_ok=True)

    # Initialize scheduler
    app.scheduler = Scheduler(app)
    # FIXME: This is ideally only run when the app is fully "started", but I
    # can't find documentation for this.
    app.scheduler.run()
    atexit_register(app.scheduler.join)

    return app
