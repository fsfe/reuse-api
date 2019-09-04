# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Request handlers for all endpoints."""

from flask import Blueprint, current_app, render_template, send_file, url_for
from flask_wtf import FlaskForm
from requests import post
from werkzeug.exceptions import HTTPException
from wtforms import BooleanField, StringField, ValidationError
from wtforms.validators import Email, InputRequired

from .models import Repository
from .scheduler import (
    NotARepository,
    determine_protocol,
    schedule_if_new_or_later,
)


# Blueprint for all endpoints delivering human-readable HTML/SVG content
html_blueprint = Blueprint("html", __name__)

# Blueprint for all endpoints delivering machine-readable JSON content
json_blueprint = Blueprint("json", __name__)

# Start page
@html_blueprint.route("/")
def index():
    return render_template("index.html")


# Filter for a project URL
def sanitize_project_url(data):
    if data is not None:
        p = data.find("://")
        if p != -1:
            data = data[p + 3 :]  # noqa
        if data.lower().endswith(".git"):
            data = data[:-4]
    return data


# Validation of a project URL
def validate_project_url(form, field):
    try:
        determine_protocol(field.data)
    except NotARepository:
        raise ValidationError("Not a Git repository")
    if Repository.is_registered(field.data):
        raise ValidationError("Project is already registered")


# Registration form
class RegisterForm(FlaskForm):
    name = StringField(label="Your name", validators=[InputRequired()])
    confirm = StringField(
        label="Your email",
        description=(
            "We need your email address to contact you in case of important "
            "changes to this service. If you would like to be informed about "
            "important updates on REUSE and the FSFE, please tick the "
            "optional box further down."
        ),
        validators=[InputRequired(), Email()],
    )
    project = StringField(
        label="Your project URL",
        description=(
            "Please add your project URL without a schema like http:// or "
            "git://. We automatically try git, https, and http as schemas."
        ),
        filters=[sanitize_project_url],
        validators=[InputRequired(), validate_project_url],
    )
    wantupdates = BooleanField(
        label=(
            "I want to receive occasional information about REUSE and other "
            "FSFE activities"
        )
    )


@html_blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        response = post(
            url=current_app.config["FORMS_URL"],
            data={"appid": "reuse-api", **form.data},
            allow_redirects=False,
        )
        if not response.ok:
            return response.text, response.status_code
        return render_template("register-success.html", **form.data)
    return render_template("register.html", form=form)


@html_blueprint.route("/badge/<path:url>")
def badge(url):
    row = schedule_if_new_or_later(url, current_app.scheduler)

    if row is None:
        return send_file(f"badges/unregistered.svg", mimetype="image/svg+xml")

    current_app.logger.debug("sending badge for '%s'", row.url)
    return send_file(f"badges/{row.status}.svg", mimetype="image/svg+xml")


@html_blueprint.route("/info/<path:url>")
def info(url):
    row = schedule_if_new_or_later(url, current_app.scheduler)

    if row is None:
        return render_template("unregistered.html", url=url), 404

    return render_template(
        "info.html",
        url=row.url,
        project_name="/".join(row.url.split("/")[-2:]),
        hash=row.hash,
        status=row.status,
        lint_code=row.lint_code,
        lint_output=row.lint_output,
        last_access=(
            row.last_access.strftime("%d %b %Y %X")
            if row.last_access
            else None
        ),
        badge=url_for(
            "html.badge", url=row.url, _external=True, _scheme="https"
        ),
        info=url_for(
            "html.info", url=row.url, _external=True, _scheme="https"
        ),
        json=url_for(
            "json.status", url=row.url, _external=True, _scheme="https"
        ),
    )


# Return error messages in JSON format
@json_blueprint.errorhandler(HTTPException)
def handle_error(err):
    return {"error": err.description}, err.code


@json_blueprint.route("/status/<path:url>")
def status(url):
    row = schedule_if_new_or_later(url, current_app.scheduler)

    if row is None:
        return {"url": url, "status": "unregistered"}

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
        "badge": url_for(
            "html.badge", url=row.url, _external=True, _scheme="https"
        ),
    }
