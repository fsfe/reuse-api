# SPDX-FileCopyrightText: Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM python:3.11-alpine AS builder
WORKDIR /root
ENV PATH="$PATH:/root/.local/bin"

COPY Pipfile Pipfile.lock ./

# Upgrade / install pipx
RUN python3 -m pip install --user pipx
RUN python3 -m pipx ensurepath

# Install pipenv with pipx
RUN python3 -m pipx install pipenv

# Install pipenv with pipx
RUN pipenv requirements --dev > requirements_all.txt
RUN pipenv requirements > requirements.txt


# Development
FROM python:3.11-alpine AS dev
EXPOSE 8000

# Install Python development packages
COPY --from=builder /root/requirements_all.txt ./
RUN pip install -r requirements_all.txt

# Instal native packages
RUN apk add --no-cache git openssh-client-default

# Switch to non-root user
RUN adduser --shell "/sbin/nologin" --disabled-password fsfe
USER fsfe
WORKDIR /home/fsfe


# Production
FROM python:3.11-alpine AS prod
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
RUN adduser --shell "/sbin/nologin" --disabled-password fsfe
USER fsfe
WORKDIR /home/fsfe

# Run the WSGI server
CMD gunicorn --bind=0.0.0.0:8000 --workers=4 "reuse_api:create_app()"
