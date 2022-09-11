BUILDDIR=${PWD}/~build

.mkbuilddir:
	@mkdir -p ${BUILDDIR}

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z0-9_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)


clean:
	# cleaning
	@rm -fr dist '~build' .pytest_cache .coverage src/admin_sync.egg-info
	@find . -name __pycache__ -o -name .eggs | xargs rm -rf
	@find . -name "*.py?" -o -name ".DS_Store" -o -name "*.orig" -o -name "*.min.min.js" -o -name "*.min.min.css" -prune | xargs rm -rf


fullclean:
	@rm -rf .tox .cache
	$(MAKE) clean


lint:
	@flake8 src/
	@isort -c src/ tests/
	@black src/ tests/ --exclude ~*


docs: .mkbuilddir
	@sh docs/to_gif.sh docs/images
	@mkdir -p ${BUILDDIR}/docs
	mkdocs build


.PHONY: build docs


