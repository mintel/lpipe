-include $(shell [ -e ../.build-harness ] || curl -sSL -o ../.build-harness "https://git.io/mintel-build-harness"; echo ../.build-harness)

build: faas/build/python/zip
.PHONY: build

clean: faas/clean
.PHONY: clean
