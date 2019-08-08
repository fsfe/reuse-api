# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""A web server that handles REUSE badges."""

import atexit
import builtins
import logging
import os
import subprocess

from flask import Flask, abort, jsonify, request, send_file, url_for
from webargs.fields import Url
from webargs.flaskparser import use_kwargs
from werkzeug.exceptions import HTTPException

from . import config
from .models import Repository, init_models
from .scheduler import Scheduler, Task

_LOGGER = logging.getLogger(__name__)

__author__ = "Carmen Bianca Bakker"
__email__ = "carmenbianca@fsfe.org"
__license__ = "GPL-3.0-or-later"
__version__ = "0.1.0"


class NotARepository(Exception):
    pass


def schedule_if_new_or_later(url, scheduler):
    try:
        latest = latest_hash(url)
    except NotARepository:
        abort(400, "Not a Git repository")
    repository = Repository.find(url)

    if repository is None:
        # Create a new entry.
        _LOGGER.debug("creating new database entry for '%s'", url)
        repository = Repository.create(url=url, hash=latest)
        scheduler.add_task(Task(url, latest))

    elif repository.hash != latest:
        # Make the database entry up-to-date.
        _LOGGER.debug("'%s' is outdated", url)
        scheduler.add_task(Task(url, latest))

    else:
        _LOGGER.debug("'%s' is still up-to-date", url)

    return repository


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


def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.from_object(config)

    # TODO: Make this configurable
    logging.basicConfig(
        format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    _LOGGER.setLevel(logging.DEBUG)

    os.environ["GIT_TERMINAL_PROMPT"] = "0"

    init_models(app)

    scheduler = Scheduler(app)
    # FIXME: This is ideally only run when the app is fully "started", but I
    # can't find documentation for this.
    scheduler.run()

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
        row = schedule_if_new_or_later(url, scheduler)

        # Return the current entry in the database.
        return jsonify(
            {
                "url": row.url,
                "hash": row.hash,
                "status": row.status,
                "lint_code": row.lint_code,
                "lint_output": row.lint_output,
                "last_access": row.last_access.isoformat()
                if row.last_access
                else None,
                "badge": url_for("badge", url=row.url, _external=True),
            }
        )

    @app.route("/badge", methods=["GET"])
    @use_kwargs(repository_params)
    def badge(url):
        row = schedule_if_new_or_later(url, scheduler)

        _LOGGER.debug("sending badge for '%s'", row.url)
        return send_file(f"{row.status}.svg", mimetype="image/svg+xml")

    return app
