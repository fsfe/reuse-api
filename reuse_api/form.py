"""RegisterForm class and it's filters & validators."""

import subprocess

from flask import url_for
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, ValidationError
from wtforms.validators import Email, InputRequired

from reuse_api.db import is_registered


def is_reachable(url: str) -> bool:
    """Check if the repository is reachable via HTTPS in 5 seconds"""
    protocol = "https"
    try:
        result = subprocess.run(
            ["git", "ls-remote", f"{protocol}://{url}", "HEAD"],
            stdout=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False

    return result.returncode == 0


def sanitize_url(url: str) -> str:
    """Filter removing schema and extension from an URL"""
    if url:
        if (scheme := url.find("://")) != -1:
            url = url[scheme + 3 :]  # noqa: E203
        if url.lower().endswith(".git"):
            url = url[:-4]
    return url


class RegisterForm(FlaskForm):
    """Form class for repository registration page"""

    @staticmethod  # noqa as form is required
    def _validate_url(form, url_field) -> None:  # noqa: ARG004
        """Check if URL is an unregistered git repository"""
        try:
            determine_protocol(url_field.data)
        except InvalidRepositoryError:
            raise ValidationError("Not a Git repository")

        if Repository.is_registered(url_field.data):
            info_page: str = url_for("html.info", url=url_field.data, _external=False)
            raise ValidationError(
                f'Project is <a href="{info_page}">already registered</a>.'
            )

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
        validators=[InputRequired(), _validate_url],
    )
    wantupdates = BooleanField(
        label=(
            "I want to receive occasional information about REUSE and other "
            "FSFE activities"
        )
    )
