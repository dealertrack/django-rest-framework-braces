.PHONY: clean-pyc clean-build docs clean

TEST_FLAGS=--verbosity=2
COVER_FLAGS=--source=drf_braces


help:  ## show help
	@grep -E '^[a-zA-Z_\-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		cut -d':' -f1- | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## install all requirements including for testing
	pip install -r requirements-dev.txt

install-quite:  ## same as install but pipes all output to /dev/null
	pip install -r requirements-dev.txt > /dev/null

clean: clean-build clean-pyc clean-test-all  ## remove all artifacts

clean-build:  ## remove build artifacts
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info

clean-pyc:  ## remove Python file artifacts
	-@find . -name '*.pyc' -follow -print0 | xargs -0 rm -f &> /dev/null
	-@find . -name '*.pyo' -follow -print0 | xargs -0 rm -f &> /dev/null
	-@find . -name '__pycache__' -type d -follow -print0 | xargs -0 rm -rf &> /dev/null

clean-test:  ## remove test and coverage artifacts
	rm -rf .coverage coverage*
	rm -rf tests/.coverage test/coverage*
	rm -rf htmlcov/

clean-test-all: clean-test  ## remove all test-related artifacts including tox
	rm -rf .tox/

lint:  ## check style with flake8
	flake8 drf_braces tests
	importanize drf_braces tests --ci

test:  ## run tests quickly with the default Python
	python tests/manage.py test ${TEST_FLAGS}

coverage: clean-test  ## run tests with coverage report
	coverage run ${COVER_FLAGS} tests/manage.py test ${TEST_FLAGS}
	coverage report -m
	coverage html

test-all:  ## run tests on every Python version with tox
	tox

check: clean-build clean-pyc clean-test lint coverage  ## run all necessary steps to check validity of project

release: clean  ## package and upload a release
	python setup.py sdist bdist_wheel upload

dist: clean
	python setup.py sdist bdist_wheel
	ls -l dist
