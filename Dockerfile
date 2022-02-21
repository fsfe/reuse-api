# SPDX-FileCopyrightText: Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM bitnami/python:3.8 AS builder

EXPOSE 8000

WORKDIR /root

# Upgrade / install required packages
RUN install_packages git openssh-client
# Upgrade setuptools and pip (https://github.com/bitnami/bitnami-docker-python/issues/13)
RUN pip3 install --no-cache-dir -U pip
# Remove pre-installed setuptools version
RUN rm -r /opt/bitnami/python/lib/python3.8/site-packages/setuptools*
# Install pipenv and setuptools
RUN pip3 install --no-cache-dir -U pipenv setuptools

# Import Python packages
COPY Pipfile Pipfile.lock ./


FROM builder AS dev
# Install Python development packages
RUN pipenv install --dev --system


FROM builder AS prod
# Install Python packages
RUN pipenv install --system --deploy

# Install the actual application
COPY . .
RUN ./setup.py install

# Switch to non-root user
RUN adduser --uid 1000 --gecos "FSFE" --shell "/sbin/nologin" --disabled-password fsfe
USER fsfe
WORKDIR /home/fsfe

# Run the WSGI server
CMD gunicorn --bind 0.0.0.0:8000 "reuse_api:create_app()"
