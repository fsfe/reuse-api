# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Request handlers for all endpoints."""

from flask import Blueprint, current_app, send_file, url_for
from webargs.fields import Url
from webargs.flaskparser import use_kwargs
from werkzeug.exceptions import HTTPException

from .scheduler import schedule_if_new_or_later


# Blueprint for all endpoints delivering human-readable HTML/SVG content
html_blueprint = Blueprint("html", __name__)

# Blueprint for all endpoints delivering machine-readable JSON content
json_blueprint = Blueprint("json", __name__)

# Parameter definition for all blueprints needing a repository URL
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


@html_blueprint.route("/badge", methods=["GET"])
@use_kwargs(repository_params)
def badge(url):
    row = schedule_if_new_or_later(url, current_app.scheduler)

    current_app.logger.debug("sending badge for '%s'", row.url)
    return send_file(f"{row.status}.svg", mimetype="image/svg+xml")


# Return error messages in JSON format
@json_blueprint.errorhandler(HTTPException)
def handle_error(err):
    if hasattr(err, "data") and "messages" in err.data:  # webargs error
        return {"error": err.data["messages"]}, err.code
    else:
        return {"error": err.description}, err.code


@json_blueprint.route("/api/project", methods=["GET"])
@use_kwargs(repository_params)
def api_project(url):
    row = schedule_if_new_or_later(url, current_app.scheduler)

    # Return the current entry in the database.
    return {
        "url": row.url,
        "hash": row.hash,
        "status": row.status,
        "lint_code": row.lint_code,
        "lint_output": row.lint_output,
        "last_access": row.last_access.isoformat()
        if row.last_access
        else None,
        "badge": url_for("html.badge", url=row.url, _external=True),
    }
