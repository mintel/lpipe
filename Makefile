.DEFAULT_GOAL := help

SHELL=/bin/bash

CURRENT_VENV := $(shell python -c 'from __future__ import print_function; import sys; print(sys.prefix if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix) else "", end="")')

ifeq ($(CURRENT_VENV),)
  VIRTUALENV := .venv
else
  VIRTUALENV := $(CURRENT_VENV)
endif

VENV_WORKDIR ?= .

ifeq ($(VENV_WORKDIR),.)
  PIPENV := PIPENV_VENV_IN_PROJECT=1 pipenv
else
  PIPENV := PIPENV_VENV_IN_PROJECT= WORKON_HOME='$(shell realpath $(VENV_WORKDIR))' pipenv
  # if the venv doesn't exist then this will fail, so it will make the VIRTUALENV will be empty
  VIRTUALENV := $(shell $(PIPENV) --venv 2> /dev/null)
  ifneq ($(.SHELLSTATUS),0)
    # means pipenv failed, so it doesn't exist yet. Need to cause a make env
    _ := $(shell $(value PIPENV) install --dev --deploy)
    # this next section doesn't work on the Jenkins box, so don't catch errors
    VIRTUALENV := $(shell $(PIPENV) --venv 2> /dev/null)
  endif
endif

WITH_PIPENV := $(PIPENV) run

PYTEST := AWS_DEFAULT_REGION=us-east-1 $(WITH_PIPENV) pytest

BLACK_TARGETS := $(shell find . -name "*.py" -not -path "*/.venv/*" -not -path "*/.tox/*")

DOCKER_COMPOSE_INT_FILES:="-f docker/docker-compose.base.yml"
DOCKER_CONFIG:=$(shell echo $(DOCKER_COMPOSE_INT_FILES))

# This python script generates the help for this Makefile.
define PRINT_HELP_PYSCRIPT
from __future__ import print_function
import re, sys

def print_formatted(target, hlp, indent=20):
    print(("%%-%ss %%s" % (indent,)) % (target, hlp))

def print_makefile_help():
    for line in sys.stdin:
        match = re.match(r'^([a-zA-Z_-]+)\s*:.*?## (.*)$$', line)
        if match:
            target, help = match.groups()
            print_formatted(target, help)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_makefile_help()
    else:
        print_formatted(*sys.argv[1:])
endef
export PRINT_HELP_PYSCRIPT

help:
	@echo "Commands:"
	@echo ""
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)
	@echo ""
	@echo ""
	@echo "Environment Variables:"
	@echo ""
	@python -c "$$PRINT_HELP_PYSCRIPT" VENV_WORKDIR "Create the development virtualenv in this directory. Default: ."
	@echo ""
.PHONY: help
.DEFAULT_GOAL := help

env: $(VIRTUALENV) ## create development virtualenv
.PHONY: env

$(VIRTUALENV): $(VENV_WORKDIR)/activate  ## create development virtualenv

$(VENV_WORKDIR)/activate: Pipfile.lock
	$(PIPENV) install --dev --deploy
	if [[ "$(VENV_WORKDIR)" == "." ]]; then touch "$$($(PIPENV) --venv 2> /dev/null)/bin/activate"; fi
	ln -fs "$$($(PIPENV) --venv 2> /dev/null)/bin/activate" $(VENV_WORKDIR)/activate

Pipfile.lock: Pipfile
	$(PIPENV) lock

build-docs: $(VIRTUALENV)  ## Build HTML docs into the `docs/_build/html` dir
	$(WITH_PIPENV) $(MAKE) -C docs clean html
.PHONY: build-docs

isort: env ## automatically sort Python imports
	$(WITH_PIPENV) isort --recursive lpipe tests conftest.py setup.py
.PHONY: isort

fmt: env
	$(WITH_PIPENV) isort --apply
	$(WITH_PIPENV) black $(BLACK_TARGETS)
.PHONY: fmt

lint: env ## check style with flake8
	$(WITH_PIPENV) black --check $(BLACK_TARGETS)
.PHONY: lint

test: $(VIRTUALENV) clean-pyc
	$(PYTEST) --junitxml=reports/python.unittest.xml
.PHONY: test

ftest: env reports/ ## run tests in a single environment, skipping Docker tests
	$(PYTEST) --no-localstack --junitxml=reports/python.unittest.xml
.PHONY: ftest

release_patch: $(VIRTUALENV) ## increment the patch version number (i.e. 1.0.0 -> 1.0.1) and do a release.
	$(WITH_PIPENV) bumpversion patch --verbose
	git push --follow-tags
.PHONY: release_patch

release_minor: $(VIRTUALENV) ## increment the minor version number (i.e. 1.0.0 -> 1.1.0) and do a release.
	bumpversion minor --verbose
	git push --follow-tags
.PHONY: release_minor

release_major: $(VIRTUALENV) ## increment the major version number (i.e. 1.0.0 -> 2.0.0) and do a release.
	bumpversion major --verbose
	git push --follow-tags
.PHONY: release_major

clean: clean-build clean-pyc clean-env clean-test clean-docs  ## remove all build, test, coverage and Python artifacts
.PHONY: clean

clean-docs:  ## remove docs build artifacts
	rm -rf docs/_build/*
.PHONY: clean-docs

clean-build:  ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
.PHONY: clean-build

clean-pyc:  ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
.PHONY: clean-pyc

clean-env:  ## remove development virtualenv
	pipenv --rm || true
.PHONY: clean-env

clean-test:  ## remove test and coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr coverage.xml
	rm -fr junit.xml
	rm -fr junit-*.xml
.PHONY: clean-test

dist: clean-build env  ## build a Python src distribution package
	$(WITH_PIPENV) python3 utils/generate_requirements.py
	$(WITH_PIPENV) python setup.py sdist
.PHONY: dist
