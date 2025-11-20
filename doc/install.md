<!--
SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# How to install reuse-api

The `Dockerfile` contains build instructions for a Docker container in which
reuse-api can run.

## Automatic deployment

reuse-api uses [drone](https://drone.fsfe.org) to automatically deploy updates
to the production server.

Upon each push to the master branch of the git repository, drone creates a
temporary clone of the repository and then sequentially executes the following
steps defined in `.drone.yml`:

1. *build-quality*: use `docker-compose` with `docker-compose-quality.yml`
   as a wrapper around `Dockerfile-quality` to create a docker image for
   automatic quality checks.

2. *quality*: in a container with the previously created image, run a number of
   quality checks to ensure no obviously broken code is deployed to the
   production server.

3. *deploy*: again, use `docker-compose`, this time to create the actual
   docker image and start the corresponding container. The file
   `docker-compose.yml` defines the parameters for this step, referring to
   the `Dockerfile` described in the previous section.


## Secrets

The following secrets are [managed in drone](http://docs.drone.io/manage-secrets/):

| Name         | Used by             | Requirement                                                      |
|--------------|---------------------|------------------------------------------------------------------|
| `secret_key` | Flask               | Arbitarily assigned. Should remain constant over server rebuilds |
| `admin_key`  | Protected functions | Strong enough, known to REUSE API admins                         |
