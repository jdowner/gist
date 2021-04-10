SHELL=/bin/bash

TEST_FILES:=$(wildcard tests/*.py)
SRC_FILES:=$(wildcard gist/*.py)

REQ_BINS := poetry
$(foreach bin,$(REQ_BINS),\
    $(if $(shell which $(bin) 2> /dev/null),,$(error Missing required package `$(bin)`)))

.PHONY: build test lint tox clean export

.poetry-install-run:
	@poetry install --remove-untracked
	@touch .poetry-install-run

build:
	@poetry build

test: .poetry-install-run
	@poetry run pytest --ff -x -v -s tests

lint: .poetry-install-run
	@poetry run black --quiet --check $(TEST_FILES) $(SRC_FILES)
	@poetry run flake8 $(TEST_FILES) $(SRC_FILES)

tox: .poetry-install-run
	@poetry run tox

clean:
	git clean -xdf

export:
	@poetry export --without-hashes -o requirements.txt
	@poetry export --dev --without-hashes -o requirements-dev.txt
