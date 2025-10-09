# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
from datetime import datetime

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm

from .config import NB_REPOSITORY_BY_PAGINATION


db = SQLAlchemy()


class Repository(db.Model):
    """Repository database class"""

    url = db.Column(db.String, primary_key=True)
    hash = db.Column(db.String(40))
    status = db.Column(db.String(13), default="initialising")
    lint_code = db.Column(db.SmallInteger)
    lint_output = db.Column(db.Text)
    spdx_output = db.Column(db.Text)
    last_access = db.Column(db.DateTime())

    @staticmethod
    def is_registered(url):
        """
        Ensure the user is registered and has validated their email from the `forms` app
        """
        with open(current_app.config["FORMS_FILE"]) as f:
            for project in json.load(f):
                if project["include_vars"]["project"].lower() == url.lower():
                    return True
        return False

    @classmethod
    def create(cls, **kwargs):
        """
        Create a new database entry for the url if project is registered
        """
        if not cls.is_registered(kwargs.get("url")):
            current_app.logger.debug(
                "there is no valid registration for '%s'", kwargs.get("url")
            )
            return None
        record = cls(**kwargs)
        db.session.add(record)
        db.session.commit()
        return record

    @classmethod
    def find(cls, url):
        """
        Try to find database entry by URL
        """
        return cls.query.filter(
            db.func.lower(cls.url) == db.func.lower(url)
        ).one_or_none()

    @classmethod
    def projects(cls, page=1):
        """
        Produce a list of compliant repos, sorted by last_access, and paginate
        """
        return (
            cls.query.order_by(cls.last_access.desc())
            .filter(cls.status == "compliant")
            .options(orm.load_only(cls.url))
            .paginate(page=page, per_page=NB_REPOSITORY_BY_PAGINATION)
        )

    @classmethod
    def all_projects(cls):
        """
        Produce a list of all repos in the database with some of their
        information
        """
        repos = []
        for repo in cls.query.all():
            repos.append(
                {
                    "url": repo.url,
                    "status": repo.status,
                    "hash": repo.hash,
                    "lint_code": repo.lint_code,
                    "last_access": repo.last_access,
                }
            )
        return repos

    @classmethod
    def projects_by_status(cls, repo_status):
        """
        Produce a list of all repos in the database with some of their
        information filtered by status
        """
        repos = []
        for repo in cls.query.all():
            repos.append(
                {
                    "url": repo.url,
                    "status": repo.status,
                    "hash": repo.hash,
                    "lint_code": repo.lint_code,
                    "last_access": repo.last_access,
                }
            )
        filtered_repositories = [
            repo for repo in repos if repo["status"] == repo_status
        ]
        return filtered_repositories

    def update(self, url, hash, status, lint_code, lint_output, spdx_output):
        """Update the database entry of a Repository"""
        self.url = url
        self.hash = hash
        self.status = status
        self.lint_code = lint_code
        self.lint_output = lint_output
        self.spdx_output = spdx_output
        self.last_access = datetime.utcnow()
        db.session.commit()
