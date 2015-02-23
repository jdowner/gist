SHELL=/bin/bash
PYTHON2=$(shell which python2)
PYTHON3=$(shell which python3)
FILES=gist/gist.py bin/gist

build:
	python setup.py build

install: build
	sudo python setup.py install \
		--record installed-files.txt \
		--single-version-externally-managed

uninstall:
	@if [ -e "installed-files.txt" ]; then \
		while read path; do \
			echo $${path}; \
			sudo rm -rf $${path}; \
		done < "installed-files.txt"; \
	fi

check:
	$(PYTHON2) -m pep8 $(FILES) --show-source
	$(PYTHON3) -m pep8 $(FILES) --show-source
