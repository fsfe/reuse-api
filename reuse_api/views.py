# SPDX-FileCopyrightText: 2023 DB Systel GmbH

"""Request handlers for all endpoints."""

from http import HTTPStatus

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    render_template,
    request,
    send_file,
    url_for,
)
from requests import post
from werkzeug.exceptions import HTTPException

from reuse_api import models as db
from reuse_api.form import RegisterForm

from .config import ADMIN_KEY, FORMS_URL
from .models import Repository


HTML: Blueprint = Blueprint("html", __name__)
JSON: Blueprint = Blueprint("json", __name__)


@HTML.get("/")
def index() -> str:
    return render_template("index.html", compliant_repos=len(getall()))


@HTML.get("/register")
def register_get() -> str:
    """Display the registration form."""
    form = RegisterForm()
    # Extract project's url from the request
    if request.args.get("url"):
        form.project.data = request.args.get("url")

    return render_template("register.html", form=form)


@HTML.post("/register")
def register_post() -> tuple[str, HTTPStatus]:
    """Process the registration form."""
    form = RegisterForm()

    if form.validate_on_submit():
        params = {"appid": "reuse-api", **form.data}
        params.pop("csrf_token", None)
        response = post(
            url=FORMS_URL,
            data=params,
            allow_redirects=False,
        )
        if not response.ok:
            return response.text, HTTPStatus(response.status_code)
        return (
            render_template("register-success.html", project=form.project.data),
            HTTPStatus.ACCEPTED,
        )
    return render_template("register.html", form=form), HTTPStatus.OK


@HTML.get("/badge/<path:url>")
def badge(url: str) -> Response:
    """The SVG badge for a repo"""

    result = send_file(f"badges/{db.status(url)}.svg", mimetype="image/svg+xml")

    # Disable caching for badge files
    result.cache_control.max_age = 0
    result.cache_control.must_revalidate = True
    result.cache_control.no_cache = True
    result.cache_control.no_store = True
    result.cache_control.private = True
    result.cache_control.public = False
    result.headers["Expires"] = "Thu, 01 Jan 1970 00:00:00 UTC"

    return result


@HTML.get("/info/<path:url>")
def info(url: str) -> tuple[str, HTTPStatus]:
    """General info page for repo"""

    # Handle unregistered & uninitialised
    if not Repository.is_registered(url):
        return render_template("unregistered.html", url=url), HTTPStatus.NOT_FOUND

    row = current_app.scheduler.schedule(url)

    if not Repository.is_initialised(url):
        return (
            render_template("uninitialised.html", project_name=db.name(url)),
            HTTPStatus.FAILED_DEPENDENCY,
        )

    # Handle normal records
    return (
        render_template(
            "info.html",
            url=url,
            project_name=db.name(url),
            head_hash=row.hash,
            compliant=Repository.is_compliant(url),
            lint_output=row.lint_output,
            last_access=row.last_access.strftime("%d %b %Y %X"),
            sbom=url_for("html.sbom", url=url, _external=False),
            json=url_for("json.status", url=url, _external=False),
            badge=url_for("html.badge", url=url, _external=False),
            badge_external=url_for(
                "html.badge", url=url, _external=True, _scheme="https"
            ),
            info_external=url_for(
                "html.info", url=url, _external=True, _scheme="https"
            ),
        ),
        HTTPStatus.OK,
    )


@HTML.get("/sbom/<path:url>.spdx")
def sbom(url: str) -> str:
    """SPDX SBOM in tag:value format"""
    # NOTE: This is a temporary measure to see if this feature is used
    current_app.logger.info("ASKED FOR SBOM: %s", url)

    if not Repository.is_initialised(url):
        abort(HTTPStatus.NOT_FOUND)

    row = current_app.scheduler.schedule(url)
    return row.spdx_output


# Return error messages in JSON format
@JSON.errorhandler(HTTPException)
def handle_error(err: HTTPException) -> tuple[dict, HTTPStatus]:
    """Handle HTTP errors, return as JSON"""
    return {"error": err.description}, HTTPStatus(err.code if err.code else 500)


@JSON.get("/status/<path:url>")
@JSON.get("/status/<path:url>.json")
def status(url: str) -> dict:
    """Machine-readable information about a repo in JSON format"""
    if not Repository.is_registered(url):
        abort(HTTPStatus.NOT_FOUND)

    row = current_app.scheduler.schedule(url)
    # Return the current entry in the database.
    return {
        "hash": row.hash,
        "status": row.status,
        "lint_code": row.lint_code,
        "last_access": (row.last_access.isoformat() if row.last_access else None),
    }


@HTML.get("/projects")
@HTML.get("/projects/page/<int:page>")
def projects(page: int = 1) -> str:
    """Show paginated table of compliant repositories"""
    return render_template("projects.html", compliant_list=Repository.projects(page))


# ------------------------------------------------------------------------------
# ADMINISTRATIVE FUNCTIONS
# Only accessible by providing the valid admin key via POST request
# ------------------------------------------------------------------------------
@HTML.post("/admin/reset/<path:url>")
def reset(url: str) -> str:
    """Unset the hash of a repository and trigger a new check"""

    # Check for valid admin credentials
    if request.form.get("admin_key") != ADMIN_KEY:
        abort(HTTPStatus.UNAUTHORIZED)
    # Force re-check
    repository = current_app.scheduler.schedule(url, force=True)
    # If re-check scheduled and repository actually exists
    if repository:
        return f"Repository scheduled for re-check: {url}"

    # Fall-back: repository does not exist and isn't registered
    return f"Repository not registered: {url}"
