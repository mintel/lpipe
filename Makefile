-include $(shell curl -sSL -o .build-harness "https://raw.githubusercontent.com/mintel/build-harness/master/templates/Makefile.build-harness"; echo .build-harness)

init: init-build-harness
	@make pipenv
.PHONY: init

build-docs: pipenv  ## Build HTML docs into the `docs/_build/html` dir
	$(WITH_PIPENV) $(MAKE) -C docs clean html
.PHONY: build-docs

dist: python/dist
.PHONY: dist

PYTHON_VERSION ?= 3.6
MAGIC_DATE := 19700101
FAAS_BUILD_DIST:=$(CURDIR)/dist
FAAS_BUILD_VENV:=$(FAAS_BUILD_DIST)/.venv

$(FAAS_BUILD_DIST):
	mkdir -p $(FAAS_BUILD_DIST)

$(FAAS_BUILD_VENV):
	pipenv run pip install -r <(pipenv lock -r) --upgrade --target $(FAAS_BUILD_VENV)
	@test -f dist/lpipe-*.tar.gz || (echo "Package didn't exist yet. Building now..." && make python/dist)
	pip install dist/lpipe-*.tar.gz --target=$(FAAS_BUILD_VENV) --upgrade --no-deps --ignore-requires-python

build-test-lambda: pipenv $(FAAS_BUILD_DIST) $(FAAS_BUILD_VENV)
	find -L . -path $(FAAS_BUILD_VENV) -prune -exec touch -d "$(MAGIC_DATE)" {} +
	find -L $(FAAS_BUILD_VENV) -exec touch -d "$(MAGIC_DATE)" {} +
	cd $(FAAS_BUILD_VENV) && zip $(FAAS_BUILD_DIST)/build.zip -rq *
	cd $(CURDIR)/func && zip $(FAAS_BUILD_DIST)/build.zip -r *py
	touch -d "$(MAGIC_DATE)" $(FAAS_BUILD_DIST)/build.zip
.PHONY: build

isort: env ## automatically sort Python imports
	$(WITH_PIPENV) isort --recursive lpipe tests conftest.py setup.py
.PHONY: isort

fmt: python/fmt
.PHONY: fmt

lint: python/lint
.PHONY: lint

test: pytest/test
.PHONY: test

testall: pipenv reports/ build-test-lambda
	$(WITH_PIPENV) pytest -n2 --dist=loadscope
.PHONY: test

testall-lf: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v --log-cli-level=info --lf
.PHONY: test

testall-verbose: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v -n2 --dist=loadscope --log-cli-level=info
.PHONY: test

test-post-build: build-test-lambda pytest/test-post-build
.PHONY: test-post-build

release_patch: bumpversion/release_patch
.PHONY: release_patch

release_minor: bumpversion/release_minor
.PHONY: release_minor

release_major: bumpversion/release_major
.PHONY: release_major

clean: pipenv/clean python/clean clean-build-harness
	rm -rf $(FAAS_BUILD_DIST)
.PHONY: clean
