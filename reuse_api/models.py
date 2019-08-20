# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_models(app):
    db.init_app(app)
    db.create_all(app=app)


class Repository(db.Model):
    url = db.Column(db.String, primary_key=True)
    hash = db.Column(db.String(40))
    status = db.Column(db.String(13), default="checking")
    lint_code = db.Column(db.SmallInteger)
    lint_output = db.Column(db.Text)
    last_access = db.Column(db.DateTime(timezone=True))

    @classmethod
    def create(cls, **kwargs):
        record = cls(**kwargs)
        db.session.add(record)
        db.session.commit()
        return record

    @classmethod
    def find(cls, url):
        return cls.query.filter_by(url=url).one_or_none()

    def update(self, hash, status, lint_code, lint_output):
        self.hash = hash
        self.status = status
        self.lint_code = lint_code
        self.lint_output = lint_output
        self.last_access = datetime.now()
        db.session.commit()
