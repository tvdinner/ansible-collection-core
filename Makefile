# tvdinner.core — shared foundation for the tvdinner.* collections.
#
# The Makefile is the uniform entry point (repo convention): CI runs exactly
# these targets. Tests are plain pytest with ansible installed from pip; the
# repo is copied into a collection tree (build/) so plugins can import under
# the ansible_collections.tvdinner.core namespace and molecule can find the
# roles by FQCN.

PYTHON ?= python3

.PHONY: test lint check clean build-tree molecule

# Copy (not symlink) the repo into a collection tree: ansible's collection
# loader and molecule both choke on the self-referential symlink a
# core -> ../../.. link creates. Re-synced on every run so PYTHONPATH=build
# and collections_path=build never execute a stale copy; .git and build are
# pruned so they never end up inside the collection.
build-tree:
	@rm -rf build/ansible_collections/tvdinner/core
	@mkdir -p build/ansible_collections/tvdinner/core
	@find . \( -path ./build -o -path ./.git \) -prune -o -type f -print \
		| tar -cf - -T - | tar -xf - -C build/ansible_collections/tvdinner/core

test: build-tree
	PYTHONPATH=build $(PYTHON) -m pytest tests/ -v

lint: build-tree
	$(PYTHON) -m compileall -q plugins tests
	yamllint .
	$(PYTHON) -m flake8 plugins tests --max-line-length=120 --extend-ignore=E402

check: lint test

# Same steps CI runs: the collections the roles call into are installed into
# build/ (first entry on collections_path) so local and CI resolve identically.
molecule: build-tree
	ansible-galaxy collection install -r molecule/requirements.yml -p build
	ANSIBLE_CONFIG=ansible.cfg molecule test

clean:
	rm -rf build
