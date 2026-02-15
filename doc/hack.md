# How to hack on reuse-api

## Development environment setup

Development should be done in the same container that it runs in for
maximum reproducibility. Please check the `Dockerfile` to find out
what image is used.

## Linting

This project is reuse compliant and uses `ruff` as it's technical linter.
To see it's config please visit `pyproject.toml`.

## Unit tests

Standard `pytest` is used with `coverage` and `mypy` extensions added.

## Runtime environment

In production the api needs
[forms](https://git.fsfe.org/fsfe-system-hackers/forms) to confirm
registrations via email.
If you do not want to set it up you may run the app with
`FORMS_DISABLE` envvar to register without confirmation or with
`FLASK_TESTING` to mock the server.

## Testing and debugging environment with docker-compose

You can simulate a complete environment with docker-compose and submodules.

- Clone the repository with all submodules `git submodule update --init --recursive`
- Run `make dev.up`
- Now the API, forms, and the interface to see the emails is available from your
  browser (see the URLs below).

### URLs

A number of URLs will have to be replaced manually during the whole register/confirm/view process.

* REUSE API web interface: http://localhost:27000
* See confirmation emails: http://localhost:1080
* Confirm the verification: http://localhost:8080 (you will be redirected to reuse.software after confirmation, change that back to http://localhost:27000)

### Debugging

- Check the logs with `make dev.logs`
- Clean the local files with `make dev.reset` to reset the dev env
