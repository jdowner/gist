SHELL=/bin/bash
PYTHON=/usr/bin/env python

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
	$(PYTHON) -m pytest -s -v tests

tox:
	tox --skip-missing-interpreters --develop --recreate

clean:
	git clean -xdf
