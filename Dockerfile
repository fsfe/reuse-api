# SPDX-Copyright: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM jfloff/alpine-python:3.7

EXPOSE 8000

# Install dependencies
RUN apk --no-cache add openssh-client

WORKDIR /root

# Copy sources
COPY . .

# Install the application
RUN ./setup.py install

# Switch to non-root user
RUN adduser -g "FSFE" -s "/sbin/nologin" -D fsfe
USER fsfe
WORKDIR /home/fsfe

# Run the WSGI server
CMD gunicorn --bind 0.0.0.0:8000 "reuse_api:create_app()"
