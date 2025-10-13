# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Request handlers for all endpoints."""

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_wtf import FlaskForm
from requests import post
from werkzeug.exceptions import HTTPException
from wtforms import BooleanField, StringField, ValidationError
from wtforms.validators import Email, InputRequired

from .config import ADMIN_KEY
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
    return render_template(
        "index.html", compliant_repos=Repository.projects().total
    )


# Filter for a project URL
def sanitize_project_url(data):
    """
    Convert a repository URL to domain.tld/path, removing schema and extension
    """
    if data is not None:
        scheme = data.find("://")
        if scheme != -1:
            data = data[scheme + 3 :]  # noqa
        if data.lower().endswith(".git"):
            data = data[:-4]
    return data


# Validation of a project URL
def validate_project_url(form, field):
    """Check if URL is a valid Git repo and already registered"""
    try:
        determine_protocol(field.data)
    except NotARepository:
        raise ValidationError("Not a Git repository")
    if Repository.is_registered(field.data):
        info_page = url_for("html.info", url=field.data, _external=False)
        info_page_url = f'<a href="{info_page}">here</a>'
        raise ValidationError(
            f"Project is already registered. See its REUSE status {info_page_url}."
        )


# Registration form
class RegisterForm(FlaskForm):
    """Form class for repository registration page"""

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
    """Registration form for new projects"""
    form = RegisterForm()
    if form.validate_on_submit():
        params = {"appid": "reuse-api", **form.data}
        if "csrf_token" in params:
            del params["csrf_token"]
        response = post(
            url=current_app.config["FORMS_URL"],
            data=params,
            allow_redirects=False,
        )
        if not response.ok:
            return response.text, response.status_code
        return render_template("register-success.html", **form.data)
    return render_template("register.html", form=form)


@html_blueprint.route("/badge/<path:url>")
def badge(url):
    """The SVG badge for a repo"""
    row = schedule_if_new_or_later(url, current_app.scheduler)

    if row is None:
        lint_status = "unregistered"
    else:
        current_app.logger.info(f"sending badge for '{row.url}'")
        lint_status = row.status

    result = send_file(f"badges/{lint_status}.svg", mimetype="image/svg+xml")

    # Disable caching for badge files
    result.cache_control.max_age = 0
    result.cache_control.must_revalidate = True
    result.cache_control.no_cache = True
    result.cache_control.no_store = True
    result.cache_control.private = True
    result.cache_control.public = False
    result.headers["Expires"] = "Thu, 01 Jan 1970 00:00:00 UTC"

    return result


@html_blueprint.route("/info/<path:url>")
def info(url):
    """General info page for repo"""
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
        spdx_output=row.spdx_output,
        last_access=(
            row.last_access.strftime("%d %b %Y %X")
            if row.last_access
            else None
        ),
        badge_external=url_for(
            "html.badge", url=row.url, _external=True, _scheme="https"
        ),
        badge_internal=url_for("html.badge", url=row.url, _external=False),
        info_external=url_for(
            "html.info", url=row.url, _external=True, _scheme="https"
        ),
        info_internal=url_for("html.info", url=row.url, _external=False),
        sbom=url_for("html.sbom", url=row.url, _external=False),
        json=url_for("json.status", url=row.url, _external=False),
    )


@html_blueprint.route("/sbom/<path:url>.spdx")
def sbom(url):
    """SPDX SBOM in tag:value format"""
    row = schedule_if_new_or_later(url, current_app.scheduler)

    if row is None:
        return render_template("unregistered.html", url=url), 404

    return row.spdx_output


# Return error messages in JSON format
@json_blueprint.errorhandler(HTTPException)
def handle_error(err):
    """Handle HTTP errors, return as JSON"""
    return {"error": err.description}, err.code


@json_blueprint.route("/status/<path:url>")
@json_blueprint.route("/status/<path:url>.json")
def status(url):
    """Machine-readable information about a repo in JSON format"""
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
        "spdx_output": row.spdx_output,
        "last_access": (
            row.last_access.isoformat() if row.last_access else None
        ),
        "badge": url_for(
            "html.badge", url=row.url, _external=True, _scheme="https"
        ),
    }


@html_blueprint.route("/projects")
@html_blueprint.route("/projects/page/<int:page>")
def projects(page=1):
    """Show paginated table of compliant registered repositories"""
    registered_list = Repository.projects(page)
    return render_template("projects.html", registered_list=registered_list)


# ------------------------------------------------------------------------------
# ADMINISTRATIVE FUNCTIONS
# Only accessible by providing the valid admin key via POST request
# ------------------------------------------------------------------------------
def check_admin(key):
    """Check whether provided admin key is correct, otherwise abort with 401"""
    if key != ADMIN_KEY:
        abort(401)


@html_blueprint.route("/admin/reset/<path:url>", methods=["POST"])
def reset(url):
    """Unset the hash of a repository and trigger a new check"""

    # Check for valid admin credentials
    check_admin(request.form.get("admin_key"))
    # Force re-check
    repository = schedule_if_new_or_later(
        url, current_app.scheduler, force=True
    )
    # If re-check scheduled and repository actually exists
    if repository:
        return f"Repository {url} has been scheduled for re-check\n"

    # Fall-back: repository does not exist and isn't registered
    return f"Repository {url} is not registered"


@json_blueprint.route("/admin/analytics/<string:query>.json", methods=["POST"])
def analytics(query):
    """Show certain analytics, only accessible with admin key"""

    # Check for valid admin credentials
    check_admin(request.form.get("admin_key"))

    if query == "all_projects":
        return Repository.all_projects()

    # Allow filtering repositories by status
    if query == "projects_by_status":
        if repo_status := request.form.get("status"):
            return Repository.projects_by_status(repo_status)
        return {"error": "Status parameter is missing"}

    return {"error": "Invalid analytics URL"}
