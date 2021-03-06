<!--
SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# How to hack on reuse-api

## Development environment setup

The (strongly) recommended way of developing, testing and debugging reuse-api
is to set up an isolated Python environment, called a *virtual environment* or
*venv*, to make development independent from the operating system provided
version of the required Python libraries. To make this as easy as possible,
reuse-api uses [Pipenv](https://docs.pipenv.org/en/latest/).

After cloning the git repository, just run `make virtualenv` in the git
checkout directory and the virtual environment will be completely set up.


## Coding style

reuse-api follows [PEP 8](https://pep8.org/). Additionally, imports are sorted
alphabetically; you can run `make applyisort` to let
[isort](https://pypi.org/project/isort/) do that for you. Source code is
formatted with the tool [black](https://pypi.org/project/black/); use `make
applyblack` to reformat the code before you commit.


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
- Run `chmod 600 ./api-worker/worker-setup/files` to set SSH files with the correct rights
- Go inside the `api-worker/docker-image` directory and run `docker build -t reuse-api-worker-runner .`
- Go inside the `api-worker` directory and run `docker-compose up --build -d`
- Go inside the `forms` directory and run `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d`
- Run `echo "[]" > /srv/forms/reuse-api/repos.json` that is a shared file with the `forms` API
- Run `chmod 777 /srv/reuse-api`. Otherwise, the database file cannot be created, and starting reuse-api aborts
- Go back to the root of the repository
- Copy the `.env.default` file to `.env`
- Run `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d`
- Now the api is available on `http://localhost:8081` from your browser

Note: If you go on `http://localhost:1080` you will be able to see emails normally sent to the customer. 
The link provided inside the emails can be on a subnet that you can't reach from your browser directly. So don't forget to replace the domain name by `localhost`.
After that, the API `forms` will redirect you to the `reuse` website, don't forget to change the url to `localhost:8081`.

## Automatic quality checks

The following commands are available for automatic quality checks:

* `make isort` to verify the correct sorting of imports.
* `make black` to verify the correct formatting of source code.
* `make lint` to verify the compliance with coding standards.
* `make pytest` to run the functional tests defined in the [tests](../tests)
  directory.
* `make quality` to run all of the above tests.

All these tests are also run during the deployment process, and updating the
code on the production server is refused if any of the tests fails, so it is
strongly recommended that you run `make quality` before committing any change.
