SHELL=/bin/bash
FILES=gist/gist.py gist/client.py
PYTHON=/usr/bin/env python

build:
	$(PYTHON) setup.py build

install: build
	sudo $(PYTHON) setup.py install \
		--record installed-files.txt \
		--single-version-externally-managed

uninstall:
	@if [ -e "installed-files.txt" ]; then \
		while read path; do \
			echo $${path}; \
			sudo rm -rf $${path}; \
		done < "installed-files.txt"; \
	fi

test:
	$(PYTHON) -m unittest tests/test_gist.py

lint:
	flake8 $(FILES)

tox:
	tox --skip-missing-interpreters --develop

clean:
	git clean -xdf
