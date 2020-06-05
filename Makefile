-include $(shell [ -e .build-harness ] || curl -sSL -o .build-harness "https://git.io/mintel-build-harness"; echo .build-harness)

.PHONY: init
init: bh/init
	@$(MAKE) bh/venv pipenv

build-docs: pipenv
	$(WITH_PIPENV) $(MAKE) -C docs clean html
.PHONY: build-docs

dist: python/dist
.PHONY: dist

dist-if: python/distif
.PHONY: dist-if

dummy_lambda/dist/.venv:
	$(WITH_PIPENV) pip install -r <(PIPENV_QUIET=1 pipenv --bare lock -r) --ignore-installed --target $@

build-test-lambda: python/distif
	@make dummy_lambda/dist/.venv
	pip install dist/lpipe-*.tar.gz --target=dummy_lambda/dist/.venv --upgrade --no-deps --ignore-requires-python
	@cd dummy_lambda; make build
.PHONY: build-test-lambda

dummy_lambda/dist/build.zip:
	$(MAKE) build-test-lambda

isort: env
	$(WITH_PIPENV) isort --recursive lpipe tests conftest.py setup.py
.PHONY: isort

fmt: python/fmt
.PHONY: fmt

lint: python/lint
.PHONY: lint

test: pytest
.PHONY: test

test-post-build: build-test-lambda pytest/test-post-build
.PHONY: test-post-build

testall: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -n2 --dist=loadscope
.PHONY: testall

testall-lf: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v --log-cli-level=info --lf
.PHONY: testall-lf

testall-mf: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v --log-cli-level=info --lf --maxfail=1
.PHONY: testall-mf

testall-verbose: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v -n2 --dist=loadscope --log-cli-level=info
.PHONY: testall-verbose

release_patch: changelog/release/patch bumpversion/release_patch
.PHONY: release_patch

release_minor: changelog/release/minor bumpversion/release_minor
.PHONY: release_minor

release_major: changelog/release/major bumpversion/release_major
.PHONY: release_major

.PHONY: clean
clean: python/clean/dist pipenv/clean python/clean
	@cd dummy_lambda; make clean
	@$(MAKE) bh/clean
