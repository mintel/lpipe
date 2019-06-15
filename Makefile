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
	test -f dist/lpipe-*.tar.gz || make python/dist
.PHONY: dist-if

build-test-lambda: dist-if
	pip install dist/lpipe-*.tar.gz --target=$(FAAS_BUILD_VENV) --upgrade --no-deps --ignore-requires-python
	make faas/build/python
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

testall-verbose: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v -n2 --dist=loadscope --log-cli-level=info
.PHONY: testall-verbose

release_patch: bumpversion/release_patch
.PHONY: release_patch

release_minor: bumpversion/release_minor
.PHONY: release_minor

release_major: bumpversion/release_major
.PHONY: release_major

clean: pipenv/clean python/clean faas/clean clean-build-harness
.PHONY: clean
