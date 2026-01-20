# SPDX-FileCopyrightText: 2025 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from flask import url_for
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, ValidationError
from wtforms.validators import Email, InputRequired

from .models import Repository
from .scheduler import InvalidRepositoryError, determine_protocol


class RegisterForm(FlaskForm):
    """Form class for repository registration page"""

    @staticmethod
    def __sanitize_url(url: str) -> str:
        """Remove schema and extension from an URL"""
        if url:
            if (scheme := url.find("://")) != -1:
                url = url[scheme + 3 :]  # noqa: E203
            if url.lower().endswith(".git"):
                url = url[:-4]
        return url

    @staticmethod  # noqa as form is required
    def __validate_url(form, url_field) -> None:  # noqa: ARG004
        """Check if URL is an unregistered git repository"""
        try:
            determine_protocol(url_field.data)
        except InvalidRepositoryError:
            raise ValidationError("Not a Git repository")

        if Repository.is_registered(url_field.data):
            info_page: str = url_for("html.info", url=url_field.data, _external=False)
            info_page_url: str = f'<a href="{info_page}">here</a>'
            raise ValidationError(
                f"Project is already registered. See its REUSE status {info_page_url}."
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
        filters=[__sanitize_url],
        validators=[InputRequired(), __validate_url],
    )
    wantupdates = BooleanField(
        label=(
            "I want to receive occasional information about REUSE and other "
            "FSFE activities"
        )
    )
