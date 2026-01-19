# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Flask application factory."""

import logging
from atexit import register as atexit_register
from os import R_OK, access, environ, path

from flask import Flask

from reuse_api import config
from reuse_api.views import html_blueprint, json_blueprint

from .models import db
from .scheduler import Scheduler


def create_app():
    if not access(config.FORMS_FILE, R_OK):
        raise PermissionError(
            "FORMS_FILE is not readable:", path.abspath(config.FORMS_FILE)
        )

    # create and configure the app
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config)

    # TODO: Make this configurable
    logging.basicConfig(format="[%(asctime)s] %(levelname)s: %(message)s")

    app.logger.setLevel(logging.DEBUG)

    app.logger.debug("Running config: %s", app.config)

    environ["GIT_TERMINAL_PROMPT"] = "0"

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.scheduler = Scheduler(app)
    # FIXME: This is ideally only run when the app is fully "started", but I
    # can't find documentation for this.
    app.scheduler.run()

    atexit_register(app.scheduler.join)

    # Register blueprints
    app.register_blueprint(html_blueprint)
    app.register_blueprint(json_blueprint)

    return app
