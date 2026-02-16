PYTHON ?= python
VENV ?= .venv

ifeq ($(OS),Windows_NT)
VENV_BIN := $(VENV)/Scripts
else
VENV_BIN := $(VENV)/bin
endif

PY := $(VENV_BIN)/python

.PHONY: help venv bootstrap install-dev install-docs smoke lint format typecheck test check verify docs-serve docs-build

help:
	@echo "Targets:"
	@echo "  bootstrap   Create venv + install development dependencies"
	@echo "  smoke       Run fast CLI smoke test"
	@echo "  check       Run lint + mypy + pytest"
	@echo "  verify      Run OCC suite verification"
	@echo "  docs-serve  Serve docs locally with autoreload"
	@echo "  docs-build  Build docs in strict mode"

venv:
	$(PYTHON) -m venv $(VENV)

install-dev: venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

install-docs: install-dev
	$(PY) -m pip install -e ".[docs]"

bootstrap: install-dev

smoke:
	$(PY) -m pytest -q tests/test_cli_smoke.py

format:
	$(PY) -m ruff check occ tests --fix

lint:
	$(PY) -m ruff check occ tests

typecheck:
	$(PY) -m mypy occ

test:
	$(PY) -m pytest

check: lint typecheck test

verify:
	$(PY) -m occ verify

docs-serve: install-docs
	$(PY) -m mkdocs serve

docs-build: install-docs
	$(PY) -m mkdocs build --strict
