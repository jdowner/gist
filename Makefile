SHELL=/bin/bash
FILES=gist/gist.py gist/client.py tests/test_gist.py
PYTHON=/usr/bin/env python
PYTHON_VERSION=$(shell $(PYTHON) -c 'import sys; print("%d.%d"% sys.version_info[0:2])' )

PYTHON_BLACK_VERSION_MIN=3.6
PYTHON_BLACK_VERSION_OK=$(shell $(PYTHON) -c 'import sys;\
	print(int(float("%d.%d"% sys.version_info[0:2]) >= $(PYTHON_BLACK_VERSION_MIN)))' )

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

ifeq ($(PYTHON_BLACK_VERSION_OK),1)
format:
	black $(FILES)
endif

lint:
ifeq ($(PYTHON_BLACK_VERSION_OK),1)
	black --check $(FILES)
endif
	flake8 $(FILES)

tox:
	tox --skip-missing-interpreters --develop

clean:
	git clean -xdf
