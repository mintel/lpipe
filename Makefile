-include $(shell curl -sSL -o .build-harness "https://raw.githubusercontent.com/mintel/build-harness/master/templates/Makefile.build-harness"; echo .build-harness)

init: init-build-harness
	@make pipenv
.PHONY: init

build-docs: pipenv
	$(WITH_PIPENV) $(MAKE) -C docs clean html
.PHONY: build-docs

dist: python/dist
.PHONY: dist

dist-if:
	test -f dist/lpipe-*.tar.gz || make dist
.PHONY: dist-if

dummy_lambda/dist/.venv:
	$(WITH_PIPENV) pip install -r <(pipenv lock -r) --upgrade --target dummy_lambda/dist/.venv --ignore-installed

build-test-lambda: dist-if
	@make dummy_lambda/dist/.venv
	pip install dist/lpipe-*.tar.gz --target=dummy_lambda/dist/.venv --upgrade --no-deps --ignore-requires-python
	@cd dummy_lambda; make build
.PHONY: build-test-lambda

isort: env
	$(WITH_PIPENV) isort --recursive lpipe tests conftest.py setup.py
.PHONY: isort

fmt: python/fmt
.PHONY: fmt

lint: python/lint
.PHONY: lint

test: pytest/test
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
	$(WITH_PIPENV) pytest -s -v --log-cli-level=info --lf --maxfail=2
.PHONY: testall-mf

testall-verbose: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v -n2 --dist=loadscope --log-cli-level=info
.PHONY: testall-verbose

release_patch: bumpversion/release_patch
.PHONY: release_patch

release_minor: bumpversion/release_minor
.PHONY: release_minor

release_major: bumpversion/release_major
.PHONY: release_major

clean: pipenv/clean python/clean python/clean/dist clean-build-harness
	@cd dummy_lambda; make clean
.PHONY: clean
