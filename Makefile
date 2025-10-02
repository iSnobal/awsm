.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

isort: ## using isort to sort imports
	isort -rc -v .

lint: ## check style with flake8
	flake8 awsm tests

tests: ## Run all tests
	python3 -m unittest discover awsm/tests

coverage: ## run coverage and submit
	coverage run --source awsm setup.py test
	coverage report --fail-under=75

coveralls: coverage ## run coveralls
	coveralls

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/awsm.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ awsm
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

install: clean ## install the package to the active Python's site-packages
	python3 -m pip install -e .[dev]
