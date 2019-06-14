-include $(shell curl -sSL -o .build-harness "https://raw.githubusercontent.com/mintel/build-harness/master/templates/Makefile.build-harness"; echo .build-harness)

init: init-build-harness
	@make pipenv
.PHONY: init

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

testall: pipenv reports/ build-test-lambda
	$(WITH_PIPENV) pytest -n2 --dist=loadscope
.PHONY: test

testall-lf: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v --log-cli-level=info --lf
.PHONY: test

testall-verbose: pipenv reports/ python/dist build-test-lambda
	$(WITH_PIPENV) pytest -s -v -n2 --dist=loadscope --log-cli-level=info
.PHONY: test

TEST_BUILD_PATH:=$(CURDIR)/tests/integration/dummy_lambda
build-test-lambda:
	@test -f dist/lpipe-*.tar.gz || (echo "Package didn't exist yet. Building now..." && make python/dist)
	cp Pipfile Pipfile.lock $(TEST_BUILD_PATH)
	cp dist/lpipe-*.tar.gz $(TEST_BUILD_PATH)/lpipe.tar.gz
	cd $(TEST_BUILD_PATH) && make build
.PHONY: build-test-lambda

test-post-build: build-test-lambda pytest/test-post-build
	rm -rf $(TEST_BUILD_PATH)/package
.PHONY: test-post-build

dist: python/dist
.PHONY: dist

release_patch: bumpversion/release_patch
.PHONY: release_patch

release_minor: bumpversion/release_minor
.PHONY: release_minor

release_major: bumpversion/release_major
.PHONY: release_major

clean: pipenv/clean python/clean clean-build-harness
	cd $(TEST_BUILD_PATH) && make clean
.PHONY: clean
