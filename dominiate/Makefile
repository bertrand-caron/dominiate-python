coverage:
	coverage run test.py --profile
	coverage html
.PHONY: coverage

pylint:
	$@ $$(find . -name '*.py')
.PHONY: pylint

errors:
	pylint -E $$(find . -name '*.py')
.PHONY: pylint

mypy:
	mypy test.py
.PHONY: mypy
