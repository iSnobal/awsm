.PHONY: clean clean-pyc clean-build docs help
.DEFAULT_GOAL := help

help: ## Display this help screen
	@sed -n 's/^\([A-Za-z0-9_.-]*\):.*## \(.*\)$$/\1:\2/p' $(MAKEFILE_LIST) | sort | column -t -s ':'

clean: clean-build clean-pyc ## Remove all Python artifacts

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

tests: ## Run all tests
	python3 -m unittest discover awsm/tests

install: clean ## Install the package in development mode including dependencies
	python3 -m pip install -e .[dev]

install-dev: clean ## Install the package without resolving dependencies
	python3 -m pip install --no-deps -e .[dev]
