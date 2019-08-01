# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later


import json
import os
import signal
import sys

from flask import Flask, abort, jsonify, request

from .scheduler import Scheduler

__author__ = "Carmen Bianca Bakker"
__email__ = "carmenbianca@fsfe.org"
__license__ = "GPL-3.0-or-later"
__version__ = "0.1.0"


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # if test_config is None:
    #     # load the instance config, if it exists, when not testing
    #     app.config.from_pyfile('config.py', silent=True)
    # else:
    #     # load the test config if passed in
    #     app.config.from_mapping(test_config)

    # TODO: Enable debug logging here somewhere?

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    scheduler = Scheduler()
    scheduler.run()

    def _handle_exit(sig, frame):
        """This thing makes sure that the program cleanly exits."""
        scheduler.join()
        sys.exit(1)

    signal.signal(signal.SIGINT, _handle_exit)

    @app.route("/api/project", methods=["GET"])
    def hello():
        url = request.args.get("url")
        if url is None:
            abort(400, "The query parameter 'url' is not specified")

        # TODO: The logic below is obviously not correct.
        scheduler.add_task(url)

        return jsonify({"url": url})

    # TODO: Also create an app.route for the badge itself.

    return app
