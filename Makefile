.PHONY: install format lint test report

install:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .

test:
	uv run pytest

report:
	@echo "report generation not yet implemented — see Task 9"
