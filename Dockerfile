# SPDX-FileCopyrightText: Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM alpine:3.22 AS base
# Add a system user for the service and switch CWD to his HOME
RUN adduser --system reuse-api --home=/var/lib/reuse-api --uid=1000
WORKDIR /var/lib/reuse-api
COPY . .
# Install base dependencies
RUN apk add --no-cache \
    # Flask with WTForms & email-validator for it
    py3-flask-wtf py3-email-validator \
    # ORM wrapper interface & postgres implementation
    py3-flask-sqlalchemy py3-psycopg2 \
    # HTTP library
    py3-requests \
    # WSGI HTTP server
    py3-gunicorn \
    # Required for the scripts to work
    git openssh-client-default \
    # For installing the application
    py3-pip py3-setuptools
# We do not break system packages as this is an original
# package and the dependencies are installed from the system
RUN pip install --break-system-packages .



# Development
FROM base AS dev
# Instal linter & testing packages
RUN apk add --no-cache \
    ruff \
    py3-pytest-cov \
    py3-requests-mock


# Production
FROM base AS prod
# Run the WSGI server as non-privleged user for security
EXPOSE 8000
USER reuse-api
CMD gunicorn --bind=0.0.0.0:8000 --workers=4 "reuse_api:create_app()"
