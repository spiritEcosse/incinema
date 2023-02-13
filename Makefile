#!/usr/bin/env bash


clean:
	find . -type f -name "*.pyc" -delete
	find . -type f -name "__pycache__" -delete
	find . -type f -name "*.py,cover" -delete
	find . -type f -name "coverage.lcov" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name ".coverage" -delete
	rm -fr "htmlcov"

#tests : run
tests:
	pytest --doctest-modules

#tests : coverage
tests__cov:
	pytest --cov=.

tests__cov_report:
	pytest --cov=. --cov-report=html tests/

open_html_results:
	open htmlcov/index.html
