"""RegisterForm class and it's filters & validators."""

# Validators require (form, form_field)
# ruff: noqa: ARG001, ANN001

import subprocess

from flask import url_for
from flask_wtf import FlaskForm  # type: ignore
from wtforms import BooleanField, StringField, ValidationError  # type: ignore
from wtforms.validators import Email, InputRequired  # type: ignore

from reuse_api.db import is_registered


def is_reachable(repo: str, timeout: int = 5) -> bool:
    """Check if the repository is reachable via HTTPS in <timeout> seconds."""
    protocol = "https"
    try:
        result = subprocess.run(
            ["git", "ls-remote", f"{protocol}://{repo}", "HEAD"],
            stdout=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:  # pragma: no cover
        return False

    return result.returncode == 0


def sanitize_url(url: str) -> str:
    """Filter removing schema and extension from an URL."""
    if url:
        if (scheme := url.find("://")) != -1:
            url = url[scheme + 3 :]
        if url.lower().endswith(".git"):
            url = url[:-4]
    return url


def repo_reachable(form, url_field) -> None:  # pragma: no cover
    """Assuring that the repository is reachable."""
    if not is_reachable(url_field.data):
        raise ValidationError("Git repository is not reachable")


def repo_unregistered(form, url_field) -> None:
    """Assure that the repository is not registered already."""
    if is_registered(url_field.data):  # pragma: no cover
        info_page: str = url_for("html.info", url=url_field.data, _external=False)
        raise ValidationError(
            f'Project is <a href="{info_page}">already registered</a>.'
        )


class RegisterForm(FlaskForm):
    """Form class for repository registration page."""

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
        filters=[sanitize_url],
        validators=[InputRequired(), repo_reachable, repo_unregistered],
    )
    wantupdates = BooleanField(
        label=(
            "I want to receive occasional information about REUSE and other "
            "FSFE activities"
        )
    )
