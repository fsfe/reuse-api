# SPDX-FileCopyrightText: Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM python:3.12-alpine AS builder
WORKDIR /root

# Copy pipfile for pipenv
COPY Pipfile Pipfile.lock ./

# Install pipenv
RUN apk add --no-cache pipx
ENV PATH="$PATH:/root/.local/bin"
RUN pipx install pipenv

# Generate requirements using pipenv
RUN pipenv requirements --dev > requirements_all.txt
RUN pipenv requirements > requirements.txt


# Development
FROM python:3.12-alpine AS dev
EXPOSE 8000

# Install Python development packages
COPY --from=builder /root/requirements_all.txt ./
RUN pip install -r requirements_all.txt

# Instal native packages
RUN apk add --no-cache git openssh-client-default

# Switch to non-root user
RUN adduser --system reuse-api --home=/var/lib/reuse-api --uid=1000
WORKDIR /var/lib/reuse-api
USER reuse-api


# Production
FROM python:3.12-alpine AS prod
EXPOSE 8000

# Copy requirements & application files
COPY --from=builder /root/requirements.txt ./
COPY . .

# Install Python packages
RUN pip install -r requirements.txt

# Install native packages
RUN apk add --no-cache git openssh-client-default pgloader

# Install the actual application
RUN python -m pip install .

# Switch to non-root user
RUN adduser --system reuse-api --home=/var/lib/reuse-api --uid=1000
WORKDIR /var/lib/reuse-api
USER reuse-api

# Run the WSGI server
CMD gunicorn --bind=0.0.0.0:8000 --workers=4 "reuse_api:create_app()"
