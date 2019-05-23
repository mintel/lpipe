-include $(shell curl -sSL -o .build-harness "https://raw.githubusercontent.com/mintel/build-harness/master/templates/Makefile.build-harness"; echo .build-harness)

init: init-build-harness
	@make pipenv
.PHONY: init

#$(VENV_WORKDIR)/activate: pipenv
#	if [[ "$(VENV_WORKDIR)" == "." ]]; then touch "$$($(PIPENV) --venv 2> /dev/null)/bin/activate"; fi
#	ln -fs "$$($(PIPENV) --venv 2> /dev/null)/bin/activate" $(VENV_WORKDIR)/activate

build-docs: pipenv  ## Build HTML docs into the `docs/_build/html` dir
	$(WITH_PIPENV) $(MAKE) -C docs clean html
.PHONY: build-docs

isort: env ## automatically sort Python imports
	$(WITH_PIPENV) isort --recursive lpipe tests conftest.py setup.py
.PHONY: isort

fmt: python/fmt
.PHONY: fmt

lint: python/lint
.PHONY: lint

test: pytest/test
.PHONY: test

ftest: pipenv
	$(WITH_PIPENV) pytest --no-localstack
.PHONY: ftest

dist: python/dist
.PHONY: dist

release_patch: bumpversion/release_patch
.PHONY: release_patch

release_minor: bumpversion/release_minor
.PHONY: release_minor

release_major: bumpversion/release_major
.PHONY: release_major

clean: pipenv/clean python/clean clean-build-harness
	@exit 0
.PHONY: clean
