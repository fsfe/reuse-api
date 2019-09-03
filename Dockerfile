# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM fsfe/alpine-pipenv:latest

EXPOSE 8000

WORKDIR /root

# Install Alpine packages
RUN apk --no-cache add git openssh-client

# Install Python packages
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

# Install the actual application
COPY . .
RUN ./setup.py install

# Switch to non-root user
RUN adduser -g "FSFE" -s "/sbin/nologin" -D fsfe
USER fsfe
WORKDIR /home/fsfe

# Run the WSGI server
CMD gunicorn --bind 0.0.0.0:8000 "reuse_api:create_app()"
