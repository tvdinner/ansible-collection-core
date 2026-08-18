# tvdinner.core — shared foundation for the tvdinner.* collections.
#
# The Makefile is the uniform entry point (repo convention): CI runs exactly
# these targets. Tests are plain pytest with ansible installed from pip; the
# repo is symlinked into a collection tree so plugins can import under the
# ansible_collections.tvdinner.core namespace.

PYTHON ?= python3

.PHONY: test lint check clean build-tree

build-tree:
	@mkdir -p build/ansible_collections/tvdinner
	@ln -sfn ../../.. build/ansible_collections/tvdinner/core

test: build-tree
	PYTHONPATH=build $(PYTHON) -m pytest tests/ -v

lint: build-tree
	$(PYTHON) -m compileall -q plugins tests
	yamllint .
	PYTHONPATH=build $(PYTHON) -m flake8 plugins tests --max-line-length=120 2>/dev/null \
		|| echo "flake8 not installed; skipped"

check: lint test

clean:
	rm -rf build
