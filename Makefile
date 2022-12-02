# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

SOURCE_DIR = reuse_api
# Files/dirs to be checked by pylama/black/isort
QUALITY_TARGETS = $(SOURCE_DIR) tests/* *.py

export FLASK_SKIP_DOTENV = 1
export FLASK_APP = ${SOURCE_DIR}
export FLASK_ENV = development
export FLASK_RUN_HOST = localhost
export FLASK_RUN_PORT = 8000

.DEFAULT_GOAL := help

COMPOSE := docker compose

GREEN  = $(shell tput -Txterm setaf 2)
WHITE  = $(shell tput -Txterm setaf 7)
YELLOW = $(shell tput -Txterm setaf 3)
RESET  = $(shell tput -Txterm sgr0)

HELPME = \
	%help; \
	while(<>) { push @{$$help{$$2 // 'options'}}, [$$1, $$3] if /^([a-zA-Z\-]+)\s*:.*\#\#(?:@([a-zA-Z\-]+))?\s(.*)$$/ }; \
	for (sort keys %help) { \
	print "${WHITE}$$_:${RESET}\n"; \
	for (@{$$help{$$_}}) { \
	$$sep = " " x (20 - length $$_->[0]); \
	print "  ${YELLOW}$$_->[0]${RESET}$$sep${GREEN}$$_->[1]${RESET}\n"; \
	}; \
	print "\n"; }

help:
	@perl -e '$(HELPME)' $(MAKEFILE_LIST)
.PHONY: help

virtualenv:  ##@development Set up the virtual environment with the Python dependencies.
	@pipenv install --dev
.PHONY: virtualenv

applyisort:  ##@development Apply a correct Python import sort inline.
	@pipenv run isort $(QUALITY_TARGETS)
.PHONY: applyisort

applyblack:  ##@development Apply source code formatting with black.
	@pipenv run black $(QUALITY_TARGETS)
.PHONY: applyblack

flask:  ##@development Run the Flask built-in web server.
	@pipenv run flask run
.PHONY: flask

gunicorn:  ##@development Run the Gunicorn based web server.
	@pipenv run gunicorn --bind $$FLASK_RUN_HOST:$$FLASK_RUN_PORT "$$FLASK_APP:create_app()"
.PHONY: gunicorn

isort:  ##@quality Check the Python source code for import sorting.
	@pipenv run isort --check --diff $(QUALITY_TARGETS)
.PHONY: isort

black:  ##@quality Check the Python source code formatting with black.
	@pipenv run black --check --diff $(QUALITY_TARGETS)
.PHONY: black

pylama:  ##@quality Check the Python source code for coding standards compliance.
	@pipenv run pylama $(QUALITY_TARGETS)
.PHONY: pylama

pytest:  ##@quality Run the functional tests.
	@pipenv run pytest --cov=$(SOURCE_DIR) tests
.PHONY: pytest

dev: ##@development Bring up entire environment with docker compose
	@docker network create forms_default || echo "Network already present."
	@$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml \
		-f forms/docker-compose.yml -f forms/docker-compose.dev.yml up

dev.up: ##@development Bring up entire environment with docker compose and detach
	@$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml \
		-f forms/docker-compose.yml -f forms/docker-compose.dev.yml up -d

dev.down: ##@development Bring down entire environment with docker compose
	@$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml \
		-f forms/docker-compose.yml -f forms/docker-compose.dev.yml down

dev.logs: ##@development Get logs of running docker containers
	@$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml \
		-f forms/docker-compose.yml -f forms/docker-compose.dev.yml logs -f

quality: isort black pylama pytest  ##@quality Run all quality checks.
.PHONY: quality
