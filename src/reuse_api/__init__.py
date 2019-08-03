# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""A web server that handles REUSE badges."""

import atexit
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
from typing import NamedTuple

from flask import (
    Flask,
    abort,
    current_app,
    g,
    jsonify,
    request,
    send_file,
    url_for,
)
from webargs.fields import Url
from webargs.flaskparser import use_kwargs
from werkzeug.exceptions import HTTPException

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


def schedule_if_new_or_later(url, app, scheduler):
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


def create_new(url, hash):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO projects VALUES (?, ?, -1, NULL, NULL, NULL)", (url, hash)
    )
    db.commit()


def latest_hash(url):
    try:
        result = subprocess.run(
            ["git", "ls-remote", url, "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise NotARepository()

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
    logging.basicConfig(
        format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    _LOGGER.setLevel(logging.DEBUG)

    os.environ["GIT_TERMINAL_PROMPT"] = "0"
    app.config.from_mapping(
        # SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, "database.sqlite"),
        # TODO: SERVERNAME
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

    atexit.register(scheduler.join)

    repository_params = {
        "url": Url(
            schemes=("git", "http", "https"),
            required=True,
            error_messages={
                "required": "Missing 'url' parameter",
                "invalid": "Invalid url for git repository",
            },
        )
    }

    # Always return error messages in JSON format
    @app.errorhandler(HTTPException)
    def handle_error(err):
        if hasattr(err, "data") and "messages" in err.data:  # webargs error
            return jsonify({"error": err.data["messages"]}), err.code
        else:
            return jsonify({"error": err.description}), err.code

    @app.route("/api/project", methods=["GET"])
    @use_kwargs(repository_params)
    def api_project(url):
        schedule_if_new_or_later(url, app, scheduler)

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
                "badge": url_for("badge", url=row.url, _external=True),
            }
        )

    @app.route("/badge", methods=["GET"])
    @use_kwargs(repository_params)
    def badge(url=None):
        schedule_if_new_or_later(url, app, scheduler)

        row = select_all(url)
        status = row.status

        if status == -1:
            image = "checking.svg"
        if status == 0:
            image = "non-compliant.svg"
        if status == 1:
            image = "compliant.svg"

        _LOGGER.debug("sending badge for '%s'", row.url)
        return send_file(image, mimetype="image/svg+xml")

    return app
