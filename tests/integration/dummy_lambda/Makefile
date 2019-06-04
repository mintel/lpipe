-include $(shell curl -sSL -o .build-harness "https://raw.githubusercontent.com/mintel/build-harness/master/templates/Makefile.build-harness"; echo .build-harness)

PYTHON_VERSION ?= 3.6
MAGIC_DATE := 19700101
build:
	mkdir -p package
	$(PIPENV) install --deploy
	pip install lpipe.tar.gz --target=$(VIRTUALENV)/lib/python$(PYTHON_VERSION)/site-packages/ --upgrade --no-deps
	# differing timestamps give us different hashes for repeated builds, so set everything the same
	find -L . -path $(VIRTUALENV) -prune -exec touch -d "$(MAGIC_DATE)" {} +
	find -L $(VIRTUALENV)/lib/python$(PYTHON_VERSION)/site-packages/ -exec touch -d "$(MAGIC_DATE)" {} +
	cd $(VIRTUALENV)/lib/python$(PYTHON_VERSION)/site-packages/ && zip $(CURDIR)/package/build.zip -rq *
	cd $(CURDIR) && zip $(CURDIR)/package/build.zip -rq *py
	touch -d "$(MAGIC_DATE)" $(CURDIR)/package/build.zip

clean:
	rm -rf package/ Pipfile* lpipe.tar.gz
