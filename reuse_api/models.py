# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
from datetime import datetime

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, orm
from sqlalchemy.engine import Engine

from .config import NB_REPOSITORY_BY_PAGINATION


db = SQLAlchemy()


class Repository(db.Model):
    url = db.Column(db.String, primary_key=True)
    hash = db.Column(db.String(40))
    status = db.Column(db.String(13), default="checking")
    lint_code = db.Column(db.SmallInteger)
    lint_output = db.Column(db.Text)
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
        if not cls.is_registered(kwargs.get("url")):
            return None
        record = cls(**kwargs)
        db.session.add(record)
        db.session.commit()
        return record

    @classmethod
    def find(cls, url):
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
            .options(orm.load_only("url"))
            .paginate(page, per_page=NB_REPOSITORY_BY_PAGINATION)
        )

    def update(self, url, hash, status, lint_code, lint_output):
        self.url = url
        self.hash = hash
        self.status = status
        self.lint_code = lint_code
        self.lint_output = lint_output
        self.last_access = datetime.utcnow()
        db.session.commit()
