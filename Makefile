# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Files/dirs to be checked
QUALITY_TARGETS = $(SOURCE_DIR) tests/* *.py

export FLASK_SKIP_DOTENV = 1
export FLASK_APP = ${SOURCE_DIR}
export FLASK_ENV = development

.DEFAULT_GOAL := help

COMPOSE := docker compose

GREEN  = $(shell tput -Txterm setaf 2)
WHITE  = $(shell tput -Txterm setaf 7)
YELLOW = $(shell tput -Txterm setaf 3)
RESET  = $(shell tput -Txterm sgr0)

HELPME = \
	%help; \
	while(<>) { push @{$$help{$$2 // 'options'}}, [$$1, $$3] if /^([a-zA-Z\-\.]+)\s*:.*\#\#(?:@([a-zA-Z\-]+))?\s(.*)$$/ }; \
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

applyblack:  ##@development Apply source code formatting with black.
	@black $(QUALITY_TARGETS)
.PHONY: applyblack

gunicorn:  ##@development Run the Gunicorn based web server.
	@gunicorn --bind localhost:8000 "reuse_api:create_app()"
.PHONY: gunicorn

black:  ##@quality Check the Python source code formatting with black.
	@black --check --diff $(QUALITY_TARGETS)
.PHONY: black

pytest:  ##@quality Run the functional tests.
	@pytest --cov=$(SOURCE_DIR)
.PHONY: pytest

dev.prep: ##@development Initially build the docker image that the API worker executes
	@chmod 600 ./api-worker/worker-setup/files/test_ed25519
	@mkdir -p ./forms/store/reuse-api
	@[ -e ./forms/store/reuse-api/repos.json ] | echo [] > ./forms/store/reuse-api/repos.json
	@docker build -f api-worker/docker-image/Dockerfile -t reuse-api-worker-runner api-worker/docker-image
.PHONY: dev.prep

dev.up: dev.prep ##@development Bring up entire environment with docker compose and detach
	@docker network create forms_default || echo "Network already present."
	@$(COMPOSE) -f forms/docker-compose.dev.yml up --build -d
	@$(COMPOSE) -f docker-compose.dev.yml       up --build -d
.PHONY: dev.up

dev.down: ##@development Bring down entire environment with docker compose
	@$(COMPOSE) -f docker-compose.dev.yml       down
	@$(COMPOSE) -f forms/docker-compose.dev.yml down
.PHONY: dev.down

dev.logs: ##@development Get logs of running docker containers
	@$(COMPOSE) -f docker-compose.dev.yml -f forms/docker-compose.dev.yml logs -f
.PHONY: dev.logs

dev.reset: ##@development Prune some configs to test the API from scratch
	@echo [] > ./forms/store/reuse-api/repos.json
	@rm -f ./api-worker/worker-setup/files/known_hosts
.PHONY: dev.reset

quality: black pytest  ##@quality Run all quality checks.
.PHONY: quality
