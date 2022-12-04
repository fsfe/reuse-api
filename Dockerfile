# SPDX-FileCopyrightText: Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM bitnami/python:3.10 AS builder
WORKDIR /root
ENV PATH="$PATH:/root/.local/bin"

# Upgrade / install pipx
RUN python3 -m pip install --user pipx
RUN python3 -m pipx ensurepath

# Install pipenv with pipx
RUN python3 -m pipx install pipenv

# Import Python packages
COPY Pipfile Pipfile.lock ./

# Install pipenv with pipx
RUN pipenv requirements --dev > requirements_all.txt
RUN pipenv requirements > requirements.txt


# Development
FROM bitnami/python:3.10 AS dev
EXPOSE 8000
RUN install_packages git openssh-client

# Install Python development packages
COPY --from=builder /root/requirements_all.txt ./
RUN pip install -r requirements_all.txt

# Switch to non-root user
RUN adduser --uid 1000 --gecos "FSFE" --shell "/sbin/nologin" --disabled-password fsfe
USER fsfe
WORKDIR /home/fsfe


# Production
FROM bitnami/python:3.10 AS prod
EXPOSE 8000
RUN install_packages git openssh-client pgloader

# Install Python packages
COPY --from=builder /root/requirements.txt ./
RUN pip install -r requirements.txt

# Install the actual application
COPY . .
RUN ./setup.py install

# Switch to non-root user
RUN adduser --uid 1000 --gecos "FSFE" --shell "/sbin/nologin" --disabled-password fsfe
USER fsfe
WORKDIR /home/fsfe

# Run the WSGI server
CMD gunicorn --bind=0.0.0.0:8000 --workers=4 "reuse_api:create_app()"
