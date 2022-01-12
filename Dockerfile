# SPDX-FileCopyrightText: Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM fsfe/pipenv:python-3.8

EXPOSE 8000

WORKDIR /root

# Install required packages
RUN apt-get -q update && \
    apt-get -qy --allow-downgrades --allow-remove-essential --allow-change-held-packages upgrade && \
    apt-get install -y git openssh-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python packages
COPY Pipfile Pipfile.lock ./
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
