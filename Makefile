.PHONY: install format lint typecheck test report

install:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy

test:
	uv run pytest

report:
	@echo "report generation not yet implemented — see Task 9"
