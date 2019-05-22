# pypedream

Data processing via distributed directed graph.


## Contents
* [API](api/modules.rst)


## Installation

```bash
pip install pypedream
```

## Develop

Use the Makefile, Luke!

```bash
$ make help
Commands:

env                  create development virtualenv
build-docs           Build HTML docs into the `site/` dir
lint                 check style with flake8
test                 run all tests
ftest                run tests in a single environment, skipping Docker tests
bumpversion_patch    increment the patch version number i.e. 1.0.0.dev0 -> 1.0.1.dev0
bumpversion_minor    increment the minor version number i.e. 1.0.0.dev0 -> 1.1.0.dev0
bumpversion_major    increment the major version number i.e. 1.0.0.dev0 -> 2.0.0.dev0
release              create a release tag from the current dev version i.e. 1.0.0.dev0 -> 1.0.0
clean                remove all build, test, coverage and Python artifacts
clean-build          remove build artifacts
clean-pyc            remove Python file artifacts
clean-env            remove development virtualenv
clean-test           remove test and coverage artifacts


Environment Variables:

VENV_WORKDIR         Create the development virtualenv in this directory
```

### Testing

Tests run using [tox](https://pypi.python.org/pypi/tox).
Some integration tests require Docker. These will be skipped if Docker is not available.

```bash
$ make test
```

To deliberately skip Docker integration tests (which can be slow):

```bash
$ make ftest
```
