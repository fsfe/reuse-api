# How to hack on reuse-api

## Development environment setup

Development should be done in the same container that it runs in for
maximum reproducibility. Please check the `Dockerfile` to find out
what image is used.

## Coding style

reuse-api follows [PEP 8](https://pep8.org/).

## Testing and debugging environment

reuse-api can be run from the git checkout directory for testing and
debugging.

Please note that reuse-api requires a running
[FSFE form server](https://git.fsfe.org/fsfe-system-hackers/forms) and SSH
access to a [REUSE lint server](https://git.fsfe.org/reuse/api-worker). The
file `repos.json` of the form server must be available in reuse-api's working
directory.

When you have set up that, you can run `make flask` to run reuse-api
with Flask's built-in web server in debug mode. Alternatively, you can run
`make gunicorn` to use the gunicorn web server, which is the variant used in
production.


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

## Automatic quality checks

The following commands are available for automatic quality checks:

* `make isort` to verify the correct sorting of imports.
* `ruff` to verify the compliance with coding standards.
* `make pytest` to run the functional tests defined in the [tests](../tests)
  directory. Please note that you may need to delete/rename your `.env`
  temporarily to avoid tests to fail.
* `make quality` to run all of the above tests.

Run these in the virtual environment to use the same versions as everyone else.

All these tests are also run during the deployment process, and updating the
code on the production server is refused if any of the tests fails, so it is
strongly recommended that you run `make quality` before committing any change.
