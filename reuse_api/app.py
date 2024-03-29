# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Flask application factory."""

import atexit
import logging
import os

from flask import Flask

from . import config
from .models import db
from .scheduler import Scheduler
from .views import html_blueprint, json_blueprint


def create_app():
    # create and configure the app
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config)

    # TODO: Make this configurable
    logging.basicConfig(
        format="[%(asctime)s] (%(name)s) %(levelname)s: %(message)s"
    )

    app.logger.setLevel(logging.DEBUG)

    os.environ["GIT_TERMINAL_PROMPT"] = "0"

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.scheduler = Scheduler(app)
    # FIXME: This is ideally only run when the app is fully "started", but I
    # can't find documentation for this.
    app.scheduler.run()

    atexit.register(app.scheduler.join)

    # Register blueprints
    app.register_blueprint(html_blueprint)
    app.register_blueprint(json_blueprint)

    return app
