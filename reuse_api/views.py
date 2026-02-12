"""Request handlers for all endpoints."""

from datetime import datetime
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

from reuse_api import db
from reuse_api.adapter import mock_add, move_registrations
from reuse_api.app import reuse_app
from reuse_api.form import RegisterForm

from .config import ADMIN_KEY, FORMS_URL
from .config import NB_REPOSITORY_BY_PAGINATION as PAGE_SIZE


HTML: Blueprint = Blueprint("html", __name__)
JSON: Blueprint = Blueprint("json", __name__)


@HTML.get("/")
def index() -> str:
    return render_template("index.html", compliant_repos=len(db.getall()))


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
        url: str | None = form.project.data
        if current_app.config.get("FORMS_DISABLE", False):
            current_app.logger.warning("Registered without forms: %s", url)
            if form.project.data:  # else branch should not happen
                db.register(form.project.data)
        elif current_app.config.get("TESTING", False):
            current_app.logger.warning("Registered with mocked forms: %s", url)
            if form.project.data:  # else branch should not happen
                mock_add(form.project.data)
        else:  # pragma: no cover
            params = {"appid": "reuse-api", **form.data}
            params.pop("csrf_token", None)
            response = post(
                url=FORMS_URL,
                data=params,
                allow_redirects=False,
            )
            if not response.ok:
                return response.text, HTTPStatus(response.status_code)
            move_registrations(str(current_app.config.get("FORMS_FILE")))
        return (
            render_template("register-success.html", project=url),
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
    if not db.is_registered(url):
        return render_template("unregistered.html", url=url), HTTPStatus.NOT_FOUND

    if not db.is_initialised(url):
        reuse_app.handle(url)
        return (
            render_template("uninitialised.html", project_name=db.name(url)),
            HTTPStatus.FAILED_DEPENDENCY,
        )
    reuse_app.handle(url)

    timestr: str = datetime.fromtimestamp(db.check_date(url)).strftime("%d %b %Y %X")
    # Handle normal records
    return (
        render_template(
            "info.html",
            url=url,
            project_name=db.name(url),
            head_hash=db.head(url),
            compliant=db.is_compliant(url),
            lint_output=db.lint(url),
            last_access=timestr,
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
def sbom(url: str) -> Response:
    """SPDX SBOM in tag:value format"""
    # NOTE: This is a temporary measure to see if this feature is used
    current_app.logger.info("ASKED FOR SBOM: %s", url)

    if not db.is_initialised(url):
        return abort(HTTPStatus.NOT_FOUND)  # pragma: no cover

    reuse_app.handle(url)

    return send_file(db.spdx_path(url))


@JSON.errorhandler(HTTPException)  # pragma: no cover
def handle_error(err: HTTPException) -> tuple[dict, HTTPStatus]:
    """Handle HTTP errors, return as JSON"""
    return {"error": err.description}, HTTPStatus(err.code if err.code else 500)


@JSON.get("/status/<path:url>")
@JSON.get("/status/<path:url>.json")
def status(url: str) -> dict:
    """Machine-readable information about a repo in JSON format"""
    if not db.is_registered(url):
        abort(HTTPStatus.NOT_FOUND)

    reuse_app.handle(url)

    timestr: str = datetime.fromtimestamp(db.check_date(url)).isoformat()
    return {
        "hash": db.head(url),
        "status": db.status(url),  # see https://git.fsfe.org/reuse/api/issues/141
        "lint_code": db.lint_rval(url),
        "last_access": timestr,
    }


@HTML.get("/projects")
@HTML.get("/projects/page/<int:page>")
def projects(page: int = 1) -> str:
    """Show paginated table of compliant repositories"""
    repos: list[str] = db.compliant_paged(page)
    has_next: bool = len(repos) == PAGE_SIZE  # HACK: will fail if len(repos)%10
    return render_template(
        "projects.html", compliant_list=repos, pg=page, has_next=has_next
    )


# ------------------------------------------------------------------------------
# ADMINISTRATIVE FUNCTIONS
# Only accessible by providing the valid admin key via POST request
# ------------------------------------------------------------------------------
@HTML.post("/admin/reset/<path:url>")
def reset(url: str) -> str:
    # Check for valid admin credentials
    if request.form.get("admin_key") != ADMIN_KEY:
        abort(HTTPStatus.UNAUTHORIZED)

    # Admin actions are executed immediately
    rval: int = db.reset(url)

    # REVIEW: this is a bit bare but I do not know how to improve it
    #         and it will not be heavily used
    return f"Reset {url} rval: {rval}"
