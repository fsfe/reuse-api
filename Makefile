# SPDX-Copyright: 2017-2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

.DEFAULT_GOAL := help

.PHONY: help
help: ## show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: clean
clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

.PHONY: clean-build
clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .cache/
	rm -fr .eggs/
	rm -fr pip-wheel-metadata/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

.PHONY: clean-pyc
clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache/

.PHONY: lint
lint: ## check with pylint
	pylint src/reuse_api tests/*.py

.PHONY: blackcheck
blackcheck: ## check with black
	black --check .

.PHONY: black
black: ## format with black
	isort -y -s build -s dist
	black .

.PHONY: reuse
reuse: dist ## check with self
	reuse lint
	tar -xf dist/reuse-api*.tar.gz -C dist/
	# This prevents the linter from using the project root as root.
	git init dist/reuse-api*/
	cd dist/reuse-api*/; reuse lint

.PHONY: test
test: ## run tests quickly
	py.test

.PHONY: coverage
coverage: ## check code coverage quickly
	py.test --cov-report term-missing --cov=src/reuse_api

.PHONY: tox
tox: ## run all tests against multiple versions of Python
	tox

.PHONY: dist
dist: clean-build clean-pyc ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

.PHONY: test-release
test-release: dist  ## package and upload to testpypi
	twine upload --sign -r testpypi dist/*

.PHONY: release
release: dist  ## package and upload a release
	twine upload --sign -r pypi dist/*

.PHONY: install-requirements
install-requirements:  ## install requirements
	pip install -r requirements.txt

.PHONY: uninstall
uninstall:  ## uninstall reuse
	-pip uninstall -y reuse-api

.PHONY: install
install: uninstall install-requirements ## install reuse
	python setup.py install

.PHONY: develop
develop: uninstall install-requirements  ## install source directory
	pre-commit install
	python setup.py develop
