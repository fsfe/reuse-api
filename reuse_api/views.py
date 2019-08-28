# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Request handlers for all endpoints."""

from flask import Blueprint, current_app, render_template, send_file, url_for
from werkzeug.exceptions import HTTPException

from .scheduler import schedule_if_new_or_later


# Blueprint for all endpoints delivering human-readable HTML/SVG content
html_blueprint = Blueprint("html", __name__)

# Blueprint for all endpoints delivering machine-readable JSON content
json_blueprint = Blueprint("json", __name__)


@html_blueprint.route("/badge/<path:url>")
def badge(url):
    row = schedule_if_new_or_later(url, current_app.scheduler)

    current_app.logger.debug("sending badge for '%s'", row.url)
    return send_file(f"badges/{row.status}.svg", mimetype="image/svg+xml")


@html_blueprint.route("/info/<path:url>")
def info(url):
    row = schedule_if_new_or_later(url, current_app.scheduler)
    return render_template(
        "info.html",
        url=row.url,
        hash=row.hash,
        status=row.status,
        lint_code=row.lint_code,
        lint_output=row.lint_output,
        last_access=(row.last_access.isoformat() if row.last_access else None),
        badge=url_for("html.badge", url=row.url, _external=True),
        json=url_for("json.status", url=row.url, _external=True),
    )


# Return error messages in JSON format
@json_blueprint.errorhandler(HTTPException)
def handle_error(err):
    if hasattr(err, "data") and "messages" in err.data:  # webargs error
        return {"error": err.data["messages"]}, err.code
    else:
        return {"error": err.description}, err.code


@json_blueprint.route("/status/<path:url>")
def status(url):
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
