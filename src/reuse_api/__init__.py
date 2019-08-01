# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""A web server that handles REUSE badges."""

import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
from typing import NamedTuple

from flask import Flask, abort, current_app, g, jsonify, request

from .db import get_db, init_app_db
from .scheduler import Scheduler, Task

_LOGGER = logging.getLogger(__name__)

__author__ = "Carmen Bianca Bakker"
__email__ = "carmenbianca@fsfe.org"
__license__ = "GPL-3.0-or-later"
__version__ = "0.1.0"


class NotARepository(Exception):
    pass


class Row(NamedTuple):
    url: str
    hash: str
    status: int
    lint_code: int
    lint_output: str
    last_access: int


def select_all(url):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM projects WHERE url=?", (url,))
    row = cur.fetchone()
    if row is None:
        # FIXME: Some kind of exception
        raise Exception()
    return Row(*row)


def create_new(url, hash):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO projects VALUES (?, ?, -1, NULL, NULL, NULL)", (url, hash)
    )
    db.commit()


def latest_hash(url):
    # FIXME!!!!: Verify that something is an URL first?
    result = subprocess.run(
        ["git", "ls-remote", url, "HEAD"], capture_output=True
    )

    if result.returncode != 0:
        raise NotARepository()
    output = result.stdout.decode("utf-8")
    return output.split()[0]


def current_hash(url):
    db = get_db()
    cur = db.execute("SELECT hash FROM projects WHERE url=?", (url,))
    result = cur.fetchone()
    if result is None:
        return None
    return result[0]


def url_exists(url):
    db = get_db()
    cur = db.execute("SELECT 1 FROM projects WHERE url=?", (url,))
    return bool(cur.fetchone())


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # TODO: Make this configurable
    logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s")
    _LOGGER.setLevel(logging.DEBUG)

    app.config.from_mapping(
        # SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, "database.sqlite")
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    scheduler = Scheduler(app)
    # FIXME: This is ideally only run when the app is fully "started", but I
    # can't find documentation for this.
    scheduler.run()

    init_app_db(app)

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

        try:
            latest = latest_hash(url)
        except NotARepository:
            abort(400, "Not a Git repository")
        with app.app_context():
            current = current_hash(url)
            exists = url_exists(url)

        # Create a bland entry.
        if not exists:
            _LOGGER.debug("creating new database entry for '%s'", url)
            with app.app_context():
                create_new(url, latest)

        # Make the database entry up-to-date.
        if not exists or current != latest:
            scheduler.add_task(Task(url, latest))
        else:
            _LOGGER.debug("'%s' is still up-to-date", url)

        # Return the current entry in the database.
        row = select_all(url)
        return jsonify(
            {
                "url": row.url,
                "hash": row.hash,
                "status": row.status,
                "lint_code": row.lint_code,
                "lint_output": row.lint_output,
                "last_access": row.last_access,
            }
        )

    # TODO: Also create an app.route for the badge itself.

    return app
