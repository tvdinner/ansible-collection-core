# tvdinner.core — shared foundation for the tvdinner.* collections.
#
# The Makefile is the uniform entry point (repo convention): CI runs exactly
# these targets. Tests are plain pytest with ansible installed from pip; the
# repo is symlinked into a collection tree so plugins can import under the
# ansible_collections.tvdinner.core namespace.

PYTHON ?= python3

.PHONY: test lint check clean build-tree molecule

build-tree:
	@mkdir -p build/ansible_collections/tvdinner
	@[ -e build/ansible_collections/tvdinner/core ] || (mkdir -p build/ansible_collections/tvdinner/core 		&& find . -path ./build -prune -o -type f -print0 | xargs -0 -I{} install -D {} build/ansible_collections/tvdinner/core/{})

test: build-tree
	PYTHONPATH=build $(PYTHON) -m pytest tests/ -v

lint: build-tree
	$(PYTHON) -m compileall -q plugins tests
	yamllint .
	$(PYTHON) -m flake8 plugins tests --max-line-length=120 --extend-ignore=E402

check: lint test

molecule:
	$(MAKE) build-tree
	ANSIBLE_CONFIG=ansible.cfg molecule test

clean:
	rm -rf build
