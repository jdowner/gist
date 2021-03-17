SHELL=/bin/bash
PYTHON=/usr/bin/env python

TEST_FILES:=$(wildcard tests/*.py)
SRC_FILES:=$(wildcard gist/*.py)
CFG_FILES:=setup.py

build:
	$(PYTHON) setup.py build

install: build
	$(PYTHON) setup.py install \
		--record installed-files.txt \
		--single-version-externally-managed

uninstall:
	@if [ -e "installed-files.txt" ]; then \
		while read path; do \
			echo $${path}; \
			rm -rf $${path}; \
		done < "installed-files.txt"; \
	fi

test:
	$(PYTHON) -m pytest --ff -x -v -s tests

lint:
	@$(PYTHON) -m black --check $(TEST_FILES) $(SRC_FILES) $(CFG_FILES)
	@$(PYTHON) -m flake8 $(TEST_FILES) $(SRC_FILES) $(CFG_FILES)

tox:
	tox --develop

clean:
	git clean -xdf

requirements:
	pip install -r requirements-test.txt
