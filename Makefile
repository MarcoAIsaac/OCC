PYTHON ?= python
VENV = .venv

.PHONY: help venv install-dev lint test verify

help:
	@echo "Targets: venv install-dev lint test verify"

venv:
	$(PYTHON) -m venv $(VENV)

install-dev:
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -e ".[dev]"

lint:
	$(VENV)/bin/ruff check .

test:
	$(VENV)/bin/pytest

verify:
	$(VENV)/bin/occ verify
